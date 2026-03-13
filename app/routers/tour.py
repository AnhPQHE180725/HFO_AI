from fastapi import APIRouter, HTTPException
from app.schemas import TourRequest, TourResponse, ModifyTourRequest
from app.config import vector_store
from app.prompts import chain, modify_chain, parser

router = APIRouter(prefix="/api/v1/tours", tags=["AI Tours"])

@router.post("/generate", response_model=TourResponse)
async def generate_tour(request: TourRequest):
    # Tăng K lên 15 để AI có đủ dữ liệu chọn lọc tọa độ gần nhau và ưu tiên nhà hàng
    retrieved_docs = vector_store.similarity_search(request.prompt, k=8)
    
    context_text = "\n".join([f"[{doc.metadata.get('type')} - ID: {doc.metadata.get('id')}] {doc.page_content}" for doc in retrieved_docs])
    
    try:
        return chain.invoke({"request": request.prompt, "context": context_text, "format_instructions": parser.get_format_instructions()})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/modify", response_model=TourResponse)
async def modify_tour(request: ModifyTourRequest):
    # Tăng K lên 10 để AI tìm quán gần với lịch trình cũ nhất
    retrieved_docs = vector_store.similarity_search(request.feedback, k=10)
    
    context_text = ""
    for d in retrieved_docs:
        doc_type = d.metadata.get("type")
        doc_id = d.metadata.get("id")
        
        if doc_type == "Dining" and doc_id in request.rejected_restaurant_ids: continue
        if doc_type == "Sightseeing" and doc_id in request.rejected_attraction_ids: continue
        
        context_text += f"[{doc_type} - ID: {doc_id}] {d.page_content}\n"
        
    try:
        return modify_chain.invoke({
            "current_tour": request.current_tour.model_dump_json(indent=2),
            "feedback": request.feedback,
            "rejected_ids": request.rejected_restaurant_ids + request.rejected_attraction_ids,
            "context": context_text,
            "format_instructions": parser.get_format_instructions()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))