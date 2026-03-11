import psycopg
from fastapi import APIRouter, HTTPException
from langchain_core.documents import Document
from app.config import PG_DIRECT_CONN, vector_store

# ĐÂY LÀ DÒNG QUAN TRỌNG NHẤT BỊ THIẾU: Khởi tạo router
router = APIRouter(prefix="/api/v1/sync", tags=["Database Sync"])

# Sử dụng @router.post thay vì @app.post
@router.post("/run")
async def sync_database():
    documents = []
    try:
        with psycopg.connect(PG_DIRECT_CONN) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT lr."LocationRestaurantId", r."RestaurantName", r."Description", r."AvgPrice", c."CategoryName", lr."Address"
                    FROM public."LocationRestaurants" lr
                    JOIN public."Restaurants" r ON lr."RestaurantId" = r."RestaurantId"
                    JOIN public."Categories" c ON r."CategoryId" = c."CategoryId"
                    WHERE r."RestaurantStatus" = 4 OR r."RestaurantStatus" = 1
                """)
                for lr_id, name, desc, price, category, address in cur.fetchall():
                    doc = Document(
                        page_content=f"Tên: {name}. ĐC: {address}. Loại: {category}. Đặc điểm: {desc}. Giá: {price}.",
                        metadata={"location_restaurant_id": lr_id, "name": name, "category": category, "price": float(price) if price else 0}
                    )
                    documents.append(doc)
        
        # Thêm vào Vector DB
        vector_store.add_documents(documents)
        return {"status": "success", "message": f"Đã đồng bộ {len(documents)} quán ăn!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))