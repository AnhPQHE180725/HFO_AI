from fastapi import APIRouter, HTTPException
from app.schemas import TourRequest, TourResponse, ModifyTourRequest
from app.config import vector_store
from app.prompts import chain, modify_chain, parser

router = APIRouter(prefix="/api/v1/tours", tags=["AI Tours"])

@router.post("/generate", response_model=TourResponse)
async def generate_tour(request: TourRequest):
    retrieved_docs = vector_store.similarity_search(request.prompt, k=4)
    context_text = "\n".join([f"[ID: {doc.metadata.get('location_restaurant_id')}] {doc.page_content}" for doc in retrieved_docs])
    try:
        return chain.invoke({"request": request.prompt, "context": context_text, "format_instructions": parser.get_format_instructions()})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/modify", response_model=TourResponse)
async def modify_tour(request: ModifyTourRequest):
    retrieved_docs = vector_store.similarity_search(request.feedback, k=6)
    context_text = "".join([f"[ID: {d.metadata.get('location_restaurant_id')}] {d.page_content}\n" for d in retrieved_docs if d.metadata.get("location_restaurant_id") not in request.rejected_ids])
    try:
        return modify_chain.invoke({
            "current_tour": request.current_tour.model_dump_json(indent=2),
            "feedback": request.feedback,
            "rejected_ids": request.rejected_ids,
            "context": context_text,
            "format_instructions": parser.get_format_instructions()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))