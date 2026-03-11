import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import psycopg
from langchain_core.documents import Document

# 1. Load cấu hình
load_dotenv(override=True)

# 2. Khởi tạo FastAPI Server
app = FastAPI(title="HFO AI Tour API", description="Microservice AI tạo lịch trình ẩm thực")

# 3. Kéo cấu hình từ .env
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
VECTOR_CONN_STRING = os.getenv("PG_VECTOR_CONN")
COLLECTION_NAME = os.getenv("VECTOR_COLLECTION")

# 4. Khởi tạo AI & Kết nối Database
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0.1)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=VECTOR_CONN_STRING,
    use_jsonb=True,
)

# ----------------- ĐỊNH NGHĨA DTOs CHUẨN KHỚP VỚI C# -----------------
class TourRequest(BaseModel):
    prompt: str = Field(..., example="Tôi muốn lịch trình 1 ngày ngon bổ rẻ ở phố cổ")

class ActivityModel(BaseModel):
    locationRestaurantId: int = Field(description="Mã ID của quán ăn (Lấy chính xác con số ID trong ngoặc vuông [ID: X] từ Context)")
    startTime: str = Field(description="Thời gian bắt đầu bữa ăn. BẮT BUỘC dùng định dạng HH:MM:00 (Ví dụ: '07:30:00', '12:00:00', '18:30:00') để C# TimeSpan parse được.")
    note: str = Field(description="1 câu ngắn gọn lý do chọn quán này (Đóng vai trò là Note)")

class DayModel(BaseModel):
    dayNumber: int = Field(description="Số thứ tự của ngày (Ví dụ: 1, 2, 3). Không được trùng lặp.")
    activities: List[ActivityModel] = Field(description="Danh sách các hoạt động (bữa ăn) trong ngày đó")

class TourResponse(BaseModel):
    title: str = Field(description="Tiêu đề của lịch trình do AI tự đặt sao cho thật lôi cuốn, hấp dẫn")
    description: str = Field(description="Mô tả ngắn gọn về trải nghiệm của cả lịch trình")
    estimatedCost: float = Field(description="Tổng chi phí ước tính (Tính tổng giá tiền các quán ăn đã chọn)")
    days: List[DayModel] = Field(description="Danh sách các ngày trong lịch trình")

class ModifyTourRequest(BaseModel):
    current_tour: TourResponse = Field(description="Toàn bộ object lịch trình hiện tại (Đã bao gồm cấu trúc lồng nhau)")
    feedback: str = Field(description="Khách muốn sửa gì? (VD: 'Đổi quán buổi tối sang ăn chè')")
    rejected_ids: List[int] = Field(default=[], description="Danh sách locationRestaurantId bị chê để AI né ra")

parser = JsonOutputParser(pydantic_object=TourResponse)

# ----------------- PROMPT -----------------
prompt_template = ChatPromptTemplate.from_messages([
    ("system", """Bạn là hệ thống API thiết kế lịch trình tự động của dự án HFO. 
    QUY TẮC BẮT BUỘC:
    1. CHỈ dùng quán ăn có trong Context. Context có định dạng: [ID: X] Tên quán...
    2. Trả về đúng 'locationRestaurantId' tương ứng với quán đã chọn.
    3. Trả về cấu trúc lồng nhau: Tour có nhiều Ngày, Ngày có nhiều Hoạt động. Tự động đánh số dayNumber.
    4. Trả về đúng định dạng JSON được yêu cầu dưới đây, KHÔNG giải thích thêm:
    
    {format_instructions}
    """),
    ("user", "Yêu cầu: {request}\n\nContext:\n{context}\n\nKết quả JSON:")
])
chain = prompt_template | llm | parser

modify_prompt_template = ChatPromptTemplate.from_messages([
    ("system", """Bạn là hệ thống API chỉnh sửa lịch trình tự động của dự án HFO. 
    QUY TẮC BẮT BUỘC:
    1. Giữ nguyên cấu trúc JSON hiện tại nếu phần đó không bị khách phàn nàn.
    2. CHỈ thay thế 'locationRestaurantId' và 'note' ở hoạt động mà khách yêu cầu đổi bằng một quán ăn phù hợp lấy từ 'Context'.
    3. TUYỆT ĐỐI KHÔNG chọn các quán có ID nằm trong 'Danh sách ID bị chê'.
    4. Cập nhật lại 'estimatedCost' nếu có thay đổi giá.
    5. KHÔNG giải thích dài dòng, trả về đúng định dạng JSON chuẩn.
    
    {format_instructions}
    """),
    ("user", "Lịch trình JSON hiện tại:\n{current_tour}\n\nYêu cầu sửa: {feedback}\n\nDanh sách ID bị chê: {rejected_ids}\n\nContext quán ăn mới để thay thế:\n{context}\n\nKết quả JSON mới:")
])
modify_chain = modify_prompt_template | llm | parser

# ----------------- API ENDPOINTS -----------------
@app.post("/api/v1/generate-tour", response_model=TourResponse)
async def generate_tour(request: TourRequest):
    retrieved_docs = vector_store.similarity_search(request.prompt, k=4) # Lấy 4 quán để đảm bảo đủ 3 bữa/ngày
    context_text = "\n".join([f"[ID: {doc.metadata.get('location_restaurant_id')}] {doc.page_content}" for doc in retrieved_docs])
    
    try:
        response_data = chain.invoke({
            "request": request.prompt,
            "context": context_text,
            "format_instructions": parser.get_format_instructions()
        })
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/modify-tour", response_model=TourResponse)
async def modify_tour(request: ModifyTourRequest):
    retrieved_docs = vector_store.similarity_search(request.feedback, k=6)
    
    context_text = ""
    for doc in retrieved_docs:
        lr_id = doc.metadata.get("location_restaurant_id")
        if lr_id not in request.rejected_ids:
            context_text += f"[ID: {lr_id}] {doc.page_content}\n"
            
    try:
        # Nhúng thẳng chuỗi JSON của request.current_tour vào prompt để AI tự bóc tách và sửa
        response_data = modify_chain.invoke({
            "current_tour": request.current_tour.model_dump_json(indent=2),
            "feedback": request.feedback,
            "rejected_ids": request.rejected_ids,
            "context": context_text,
            "format_instructions": parser.get_format_instructions()
        })
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- API ENDPOINT: ĐỒNG BỘ DỮ LIỆU TỪ SQL -----------------
@app.post("/api/v1/sync-data")
async def sync_database():
    print("\n🔄 ĐANG ĐỒNG BỘ DỮ LIỆU TỪ SQL SANG VECTOR DB...")
    
    # Lấy chuỗi kết nối SQL trực tiếp
    DIRECT_CONN = os.getenv("PG_DIRECT_CONN")
    
    documents = []
    try:
        with psycopg.connect(DIRECT_CONN) as conn:
            with conn.cursor() as cur:
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
                    content = f"Tên quán: {name}. Địa chỉ: {address}. Danh mục: {category}. Đặc điểm: {desc}. Giá: {price} VND."
                    
                    doc = Document(
                        page_content=content,
                        metadata={
                            "location_restaurant_id": lr_id, 
                            "name": name, 
                            "category": category, 
                            "price": float(price) if price else 0
                        }
                    )
                    documents.append(doc)
        
        # Lưu vào Vector DB
        vector_store.add_documents(documents)
        print(f"🎉 ĐÃ ĐỒNG BỘ THÀNH CÔNG {len(documents)} QUÁN ĂN!")
        
        return {"status": "success", "message": f"Đã đồng bộ {len(documents)} quán ăn thành công!"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đồng bộ: {str(e)}")