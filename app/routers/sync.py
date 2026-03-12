import psycopg
from fastapi import APIRouter, HTTPException
from langchain_core.documents import Document
from app.config import PG_DIRECT_CONN, vector_store

router = APIRouter(prefix="/api/v1/sync", tags=["Database Sync"])

@router.post("/run")
async def sync_database():
    documents = []
    try:
        with psycopg.connect(PG_DIRECT_CONN) as conn:
            with conn.cursor() as cur:
                # 1. Đồng bộ Quán ăn (Dining)
                cur.execute("""
                    SELECT lr."LocationRestaurantId", r."RestaurantName", r."Description", r."AvgPrice", c."CategoryName", lr."Address"
                    FROM public."LocationRestaurants" lr
                    JOIN public."Restaurants" r ON lr."RestaurantId" = r."RestaurantId"
                    JOIN public."Categories" c ON r."CategoryId" = c."CategoryId"
                    WHERE r."RestaurantStatus" = 4 OR r."RestaurantStatus" = 1
                """)
                for lr_id, name, desc, price, category, address in cur.fetchall():
                    doc = Document(
                        page_content=f"Quán ăn: {name}. ĐC: {address}. Loại: {category}. Đặc điểm: {desc}. Giá: {price}.",
                        metadata={"type": "Dining", "id": lr_id, "name": name, "price": float(price) if price else 0}
                    )
                    documents.append(doc)

                # 2. Đồng bộ Địa điểm tham quan (Sightseeing)
                cur.execute("""
                    SELECT "AttractionId", "Name", "Description", "Address"
                    FROM public."Attractions"
                """)
                for att_id, name, desc, address in cur.fetchall():
                    doc = Document(
                        page_content=f"Điểm tham quan: {name}. ĐC: {address}. Đặc điểm: {desc}.",
                        metadata={"type": "Sightseeing", "id": att_id, "name": name, "price": 0} # Điểm tham quan tạm để giá 0
                    )
                    documents.append(doc)
        
        # Thêm toàn bộ vào Vector DB
        vector_store.add_documents(documents)
        return {"status": "success", "message": f"Đã đồng bộ {len(documents)} địa điểm (Ăn uống + Tham quan)!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))