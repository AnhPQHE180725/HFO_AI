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
                # 1. Đồng bộ Quán ăn (Dining) - Kéo thêm Tọa độ
                cur.execute("""
                    SELECT lr."LocationRestaurantId", r."RestaurantName", r."Description", r."AvgPrice", c."CategoryName", lr."Address", lr."Latitude", lr."Longitude"
                    FROM public."LocationRestaurants" lr
                    JOIN public."Restaurants" r ON lr."RestaurantId" = r."RestaurantId"
                    JOIN public."Categories" c ON r."CategoryId" = c."CategoryId"
                    WHERE r."RestaurantStatus" = 4 OR r."RestaurantStatus" = 1
                """)
                for lr_id, name, desc, price, category, address, lat, lon in cur.fetchall():
                    lat_str = lat if lat else "Không rõ"
                    lon_str = lon if lon else "Không rõ"
                    doc = Document(
                        page_content=f"Quán ăn: {name}. ĐC: {address}. Tọa độ: ({lat_str}, {lon_str}). Loại: {category}. Đặc điểm: {desc}. Giá: {price}.",
                        metadata={"type": "Dining", "id": lr_id, "name": name, "price": float(price) if price else 0}
                    )
                    documents.append(doc)

                # 2. Đồng bộ Địa điểm tham quan (Sightseeing) - Kéo thêm Tọa độ
                cur.execute("""
                    SELECT "AttractionId", "Name", "Description", "Address", "Latitude", "Longitude"
                    FROM public."Attractions"
                """)
                for att_id, name, desc, address, lat, lon in cur.fetchall():
                    lat_str = lat if lat else "Không rõ"
                    lon_str = lon if lon else "Không rõ"
                    doc = Document(
                        page_content=f"Điểm tham quan: {name}. ĐC: {address}. Tọa độ: ({lat_str}, {lon_str}). Đặc điểm: {desc}.",
                        metadata={"type": "Sightseeing", "id": att_id, "name": name, "price": 0} 
                    )
                    documents.append(doc)
        
        vector_store.add_documents(documents)
        return {"status": "success", "message": f"Đã đồng bộ {len(documents)} địa điểm (Kèm tọa độ)!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))