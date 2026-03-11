import os
import psycopg
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain_core.documents import Document

load_dotenv(override=True)
CONNECTION_STRING = os.getenv("PG_DIRECT_CONN")
VECTOR_CONN_STRING = os.getenv("PG_VECTOR_CONN")
COLLECTION_NAME = os.getenv("VECTOR_COLLECTION")

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vector_store = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=VECTOR_CONN_STRING,
    use_jsonb=True,
)

print("1️⃣ Đang kết nối vào SQL lấy dữ liệu chuẩn cho C#...\n")

documents = []
with psycopg.connect(CONNECTION_STRING) as conn:
    with conn.cursor() as cur:
        # SỬA SQL CHỖ NÀY: Join với bảng LocationRestaurant để lấy LocationRestaurantId
        cur.execute("""
            SELECT lr."LocationRestaurantId", r."RestaurantName", r."Description", r."AvgPrice", c."CategoryName", lr."Address"
            FROM public."LocationRestaurants" lr
            JOIN public."Restaurants" r ON lr."RestaurantId" = r."RestaurantId"
            JOIN public."Categories" c ON r."CategoryId" = c."CategoryId"
            WHERE r."RestaurantStatus" = 4 OR r."RestaurantStatus" = 1
        """)
        
        rows = cur.fetchall()
        for row in rows:
            lr_id, name, desc, price, category, address = row
            
            # Gộp thành văn bản Context
            content = f"Tên quán: {name}. Địa chỉ: {address}. Danh mục: {category}. Đặc điểm: {desc}. Giá: {price} VND."
            
            doc = Document(
                page_content=content,
                # ÉP CHUẨN METADATA: Bắt buộc lưu location_restaurant_id
                metadata={
                    "location_restaurant_id": lr_id, 
                    "name": name, 
                    "category": category, 
                    "price": float(price) if price else 0
                }
            )
            documents.append(doc)
            print(f"✅ Đã đọc dữ liệu: [{lr_id}] {name} - {address}")

print(f"\n2️⃣ Đang chuyển đổi {len(documents)} bản ghi thành Vector...\n")
vector_store.add_documents(documents)
print("🎉 XONG! Dữ liệu đã đồng bộ.")