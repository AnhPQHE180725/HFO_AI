import math
from typing import Any, Iterable, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from langchain_core.documents import Document
import psycopg

from app.config import PG_DIRECT_CONN, vector_store
from app.prompts import chain, modify_chain, parser
from app.schemas import ModifyTourRequest, TourRequest, TourResponse

router = APIRouter(prefix="/api/v1/tours", tags=["AI Tours"])


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def _safe_similarity_search(query: str, k: int, doc_type: Optional[str]) -> List[Document]:
    try:
        if doc_type is None:
            return vector_store.similarity_search(query, k=k)
        return vector_store.similarity_search(query, k=k, filter={"type": doc_type})
    except Exception:
        raw_docs = vector_store.similarity_search(query, k=max(k * 2, 10))
        if doc_type is None:
            return raw_docs[:k]
        filtered = [d for d in raw_docs if d.metadata.get("type") == doc_type]
        return filtered[:k]


def _dedupe_docs(docs: Iterable[Document]) -> List[Document]:
    seen: set[Tuple[Any, Any]] = set()
    result: List[Document] = []
    for d in docs:
        key = (d.metadata.get("type"), d.metadata.get("id"))
        if key in seen:
            continue
        seen.add(key)
        result.append(d)
    return result


def _sort_docs_by_distance(
    docs: List[Document], user_lat: Optional[float], user_lon: Optional[float]
) -> List[Document]:
    if user_lat is None or user_lon is None:
        return docs

    def score(doc: Document):
        lat = _to_float(doc.metadata.get("latitude"))
        lon = _to_float(doc.metadata.get("longitude"))
        if lat is None or lon is None:
            return float("inf")
        return _haversine_km(user_lat, user_lon, lat, lon)

    return sorted(docs, key=score)


def _distance_text(doc: Document, user_lat: Optional[float], user_lon: Optional[float]) -> str:
    if user_lat is None or user_lon is None:
        return "unknown"
    lat = _to_float(doc.metadata.get("latitude"))
    lon = _to_float(doc.metadata.get("longitude"))
    if lat is None or lon is None:
        return "unknown"
    return f"{_haversine_km(user_lat, user_lon, lat, lon):.2f} km"


def _build_context(
    docs: List[Document], user_lat: Optional[float], user_lon: Optional[float]
) -> str:
    lines = []
    for doc in docs:
        doc_type = doc.metadata.get("type")
        doc_id = doc.metadata.get("id")
        distance = _distance_text(doc, user_lat, user_lon)
        lines.append(
            f"[{doc_type} - ID: {doc_id}] DistanceFromUser: {distance}. {doc.page_content}"
        )
    return "\n".join(lines)


def _build_planning_hint(user_lat: Optional[float], user_lon: Optional[float]) -> str:
    if user_lat is not None and user_lon is not None:
        return (
            f"User location = ({user_lat}, {user_lon}). "
            "Uu tien bat dau ngay tai diem gan user, sau do di theo cum gan nhau."
        )
    return "Khong co user location. Van toi uu theo cum dia diem dua tren toa do trong context."


def _extract_dining_ids(ai_response: dict) -> List[int]:
    ids: set[int] = set()
    for day in ai_response.get("days", []):
        for activity in day.get("activities", []):
            if activity.get("activityType") == 1:
                rid = activity.get("locationRestaurantId")
                if isinstance(rid, int) and rid > 0:
                    ids.add(rid)
    return sorted(ids)


def _compute_estimated_cost_from_db(location_restaurant_ids: List[int]) -> float:
    if not location_restaurant_ids:
        return 0.0

    try:
        with psycopg.connect(PG_DIRECT_CONN) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COALESCE(SUM(COALESCE(r."AvgPrice", 0)), 0)
                    FROM public."LocationRestaurants" lr
                    JOIN public."Restaurants" r
                        ON lr."RestaurantId" = r."RestaurantId"
                    WHERE lr."LocationRestaurantId" = ANY(%s)
                    """,
                    (location_restaurant_ids,),
                )
                row = cur.fetchone()
                return float(row[0] or 0)
    except Exception:
        # Fail-safe: if DB cost lookup has issues, do not break tour generation.
        return 0.0


def _enforce_estimated_cost_from_db(ai_response: dict) -> dict:
    dining_ids = _extract_dining_ids(ai_response)
    ai_response["estimatedCost"] = _compute_estimated_cost_from_db(dining_ids)
    return ai_response


def _collect_docs_for_generate(request: TourRequest) -> List[Document]:
    dining_docs = _safe_similarity_search(request.prompt, k=20, doc_type="Dining")
    sightseeing_docs = _safe_similarity_search(request.prompt, k=10, doc_type="Sightseeing")

    ordered_dining = _sort_docs_by_distance(
        _dedupe_docs(dining_docs), request.userLatitude, request.userLongitude
    )[:14]
    ordered_sightseeing = _sort_docs_by_distance(
        _dedupe_docs(sightseeing_docs), request.userLatitude, request.userLongitude
    )[:6]

    merged: List[Document] = []
    merged.extend(ordered_dining)

    # Interleave a few attractions while keeping dining dominant.
    for i, att in enumerate(ordered_sightseeing):
        insert_at = min(2 + i * 3, len(merged))
        merged.insert(insert_at, att)

    return _dedupe_docs(merged)


def _collect_docs_for_modify(request: ModifyTourRequest) -> List[Document]:
    query = f"{request.feedback}\n{request.current_tour.model_dump_json()}"
    dining_docs = _safe_similarity_search(query, k=20, doc_type="Dining")
    sightseeing_docs = _safe_similarity_search(query, k=10, doc_type="Sightseeing")

    rejected_restaurant_ids = set(request.rejected_restaurant_ids)
    rejected_attraction_ids = set(request.rejected_attraction_ids)

    def allowed(doc: Document) -> bool:
        doc_type = doc.metadata.get("type")
        doc_id = doc.metadata.get("id")
        if doc_type == "Dining" and doc_id in rejected_restaurant_ids:
            return False
        if doc_type == "Sightseeing" and doc_id in rejected_attraction_ids:
            return False
        return True

    merged = [d for d in _dedupe_docs(dining_docs + sightseeing_docs) if allowed(d)]
    return _sort_docs_by_distance(merged, request.userLatitude, request.userLongitude)


@router.post("/generate", response_model=TourResponse)
async def generate_tour(request: TourRequest):
    try:
        docs = _collect_docs_for_generate(request)
        context_text = _build_context(docs, request.userLatitude, request.userLongitude)
        planning_hint = _build_planning_hint(request.userLatitude, request.userLongitude)
        ai_response = chain.invoke(
            {
                "request": request.prompt,
                "planning_hint": planning_hint,
                "context": context_text,
                "format_instructions": parser.get_format_instructions(),
            }
        )
        return _enforce_estimated_cost_from_db(ai_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/modify", response_model=TourResponse)
async def modify_tour(request: ModifyTourRequest):
    try:
        docs = _collect_docs_for_modify(request)
        context_text = _build_context(docs, request.userLatitude, request.userLongitude)
        planning_hint = _build_planning_hint(request.userLatitude, request.userLongitude)
        rejected_ids = sorted(
            set(request.rejected_restaurant_ids).union(set(request.rejected_attraction_ids))
        )
        ai_response = modify_chain.invoke(
            {
                "current_tour": request.current_tour.model_dump_json(indent=2),
                "feedback": request.feedback,
                "planning_hint": planning_hint,
                "rejected_ids": rejected_ids,
                "context": context_text,
                "format_instructions": parser.get_format_instructions(),
            }
        )
        return _enforce_estimated_cost_from_db(ai_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
