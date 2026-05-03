from datetime import datetime, time, timedelta
from typing import Any, Optional

import psycopg
from fastapi import APIRouter, HTTPException
from langchain_core.documents import Document

from app.config import PG_DIRECT_CONN, vector_store

router = APIRouter(prefix="/api/v1/sync", tags=["Database Sync"])


def _time_to_hhmm(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    return str(value)


def _safe_text(value: Optional[str], fallback: str = "unknown") -> str:
    text = (value or "").strip()
    return text if text else fallback


@router.post("/run")
async def sync_database():
    documents = []
    try:
        with psycopg.connect(PG_DIRECT_CONN) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH dish_summary AS (
                        SELECT d."RestaurantId",
                               STRING_AGG(
                                    DISTINCT d."DishName" || ' (' || d."Price"::text || ' VND)',
                                    '; '
                               ) AS dishes
                        FROM public."Dishes" d
                        GROUP BY d."RestaurantId"
                    ),
                    dish_category_summary AS (
                        SELECT dc."RestaurantId",
                               STRING_AGG(DISTINCT dc."CategoryName", ', ') AS dish_categories
                        FROM public."DishCategories" dc
                        GROUP BY dc."RestaurantId"
                    ),
                    operating_hour_summary AS (
                        SELECT oh."LocationRestaurantId",
                               MIN(oh."OpenTime")  AS open_time,
                               MAX(oh."CloseTime") AS close_time
                        FROM public."OperatingHours" oh
                        WHERE oh."IsClosed" = false
                        GROUP BY oh."LocationRestaurantId"
                    )
                    SELECT
                        lr."LocationRestaurantId",
                        r."RestaurantName",
                        r."Description",
                        r."AvgPrice",
                        c."CategoryName",
                        lr."Address",
                        lr."Latitude",
                        lr."Longitude",
                        prov."Name" AS city_province,
                        w."Name" AS ward_name,
                        ds.dishes,
                        dcs.dish_categories,
                        ohs.open_time,
                        ohs.close_time
                    FROM public."LocationRestaurants" lr
                    JOIN public."Restaurants" r
                        ON lr."RestaurantId" = r."RestaurantId"
                    LEFT JOIN public."Categories" c
                        ON r."CategoryId" = c."CategoryId"
                    LEFT JOIN public."Locations" loc
                        ON lr."LocationId" = loc."LocationId"
                    LEFT JOIN public."Wards" w
                        ON loc."WardCode" = w."WardCode"
                    LEFT JOIN public."Provinces" prov
                        ON w."ProvinceCode" = prov."ProvinceCode"
                    LEFT JOIN dish_summary ds
                        ON r."RestaurantId" = ds."RestaurantId"
                    LEFT JOIN dish_category_summary dcs
                        ON r."RestaurantId" = dcs."RestaurantId"
                    LEFT JOIN operating_hour_summary ohs
                        ON lr."LocationRestaurantId" = ohs."LocationRestaurantId"
                    WHERE r."RestaurantStatus" IN (1, 4)
                    """
                )

                for (
                    lr_id,
                    name,
                    desc,
                    price,
                    category,
                    address,
                    lat,
                    lon,
                    city,
                    ward,
                    dishes,
                    dish_categories,
                    open_time,
                    close_time,
                ) in cur.fetchall():
                    content = (
                        f"Restaurant: {_safe_text(name)}. "
                        f"Address: {_safe_text(address)}. "
                        f"Area: ward={_safe_text(ward)}, city={_safe_text(city)}. "
                        f"Coordinates: ({_safe_text(lat)}, {_safe_text(lon)}). "
                        f"Category: {_safe_text(category)}. "
                        f"Average price: {float(price) if price else 0} VND. "
                        f"Open-Close: {_time_to_hhmm(open_time)}-{_time_to_hhmm(close_time)}. "
                        f"Dish categories: {_safe_text(dish_categories)}. "
                        f"Signature dishes: {_safe_text(dishes)}. "
                        f"Description: {_safe_text(desc)}."
                    )

                    documents.append(
                        Document(
                            page_content=content,
                            metadata={
                                "type": "Dining",
                                "id": lr_id,
                                "name": name,
                                "price": float(price) if price else 0,
                                "category": _safe_text(category),
                                "latitude": _safe_text(lat),
                                "longitude": _safe_text(lon),
                                "city": _safe_text(city),
                                "ward": _safe_text(ward),
                            },
                        )
                    )


                cur.execute(
                    """
                    SELECT
                        a."AttractionId",
                        a."Name",
                        a."Description",
                        a."Address",
                        a."Latitude",
                        a."Longitude",
                        a."OpenTime",
                        a."CloseTime"
                    FROM public."Attractions" a
                    """
                )

                for (
                    attraction_id,
                    name,
                    desc,
                    address,
                    lat,
                    lon,
                    open_time,
                    close_time,
                ) in cur.fetchall():
                    content = (
                        f"Attraction: {_safe_text(name)}. "
                        f"Address: {_safe_text(address)}. "
                        f"Coordinates: ({_safe_text(lat)}, {_safe_text(lon)}). "
                        f"Open-Close: {_time_to_hhmm(open_time)}-{_time_to_hhmm(close_time)}. "
                        f"Description: {_safe_text(desc)}."
                    )

                    documents.append(
                        Document(
                            page_content=content,
                            metadata={
                                "type": "Sightseeing",
                                "id": attraction_id,
                                "name": name,
                                "price": 0.0,
                                "latitude": _safe_text(lat),
                                "longitude": _safe_text(lon),
                                "open_time": _time_to_hhmm(open_time),
                                "close_time": _time_to_hhmm(close_time),
                            },
                        )
                    )

        try:
            vector_store.delete_collection()
            vector_store.create_collection()
        except Exception:
            pass

        vector_store.add_documents(documents)
        return {
            "status": "success",
            "message": f"Synced {len(documents)} places (Dining + Sightseeing) with rich metadata.",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
