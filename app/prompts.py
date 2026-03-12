from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.schemas import TourResponse
from app.config import llm

parser = JsonOutputParser(pydantic_object=TourResponse)

prompt_template = ChatPromptTemplate.from_messages([
    ("system", """Bạn là hệ thống thiết kế lịch trình CÓ CẢ ĂN UỐNG VÀ THAM QUAN.
    QUY TẮC BẮT BUỘC:
    1. CHỈ dùng dữ liệu trong Context. Context có dạng: [Loại - ID: X] Tên...
    2. Nếu chọn [Dining], BẮT BUỘC set activityType = 1, điền locationRestaurantId = X, và attractionId = null.
    3. Nếu chọn [Sightseeing], BẮT BUỘC set activityType = 2, điền attractionId = X, và locationRestaurantId = null.
    4. TUYỆT ĐỐI KHÔNG bọc kết quả trong markdown block (KHÔNG dùng ```json). Chỉ trả về chuỗi JSON thô.
    
    {format_instructions}"""),
    ("user", "Yêu cầu: {request}\n\nContext:\n{context}\n\nJSON:")
])
chain = prompt_template | llm | parser

modify_prompt_template = ChatPromptTemplate.from_messages([
    ("system", """Bạn là hệ thống sửa lịch trình CÓ CẢ ĂN UỐNG VÀ THAM QUAN.
    QUY TẮC BẮT BUỘC:
    1. Giữ nguyên JSON hiện tại nếu không phàn nàn.
    2. CHỈ thay thế các activity bị chê bằng dữ liệu lấy từ Context.
    3. Chú ý: Nếu đổi sang [Dining] thì activityType=1, nếu đổi sang [Sightseeing] thì activityType=2. Các ID không dùng phải để null.
    4. TUYỆT ĐỐI KHÔNG bọc kết quả trong markdown block (KHÔNG dùng ```json). Chỉ trả về chuỗi JSON thô.
    
    {format_instructions}"""),
    ("user", "JSON hiện tại:\n{current_tour}\nYêu cầu sửa: {feedback}\n\nContext mới:\n{context}\n\nJSON:")
])
modify_chain = modify_prompt_template | llm | parser