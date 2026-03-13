from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.schemas import TourResponse
from app.config import llm

parser = JsonOutputParser(pydantic_object=TourResponse)

prompt_template = ChatPromptTemplate.from_messages([
    ("system", """Bạn là hệ thống thiết kế lịch trình ẨM THỰC VÀ DU LỊCH.
    QUY TẮC BẮT BUỘC:
    1. ƯU TIÊN ẨM THỰC: Phần lớn lịch trình (70%-80%) BẮT BUỘC phải là các Quán ăn [Dining]. Điểm tham quan [Sightseeing] chỉ là phụ để đi dạo tiêu thực hoặc check-in xen kẽ.
    2. TỐI ƯU DI CHUYỂN: Hãy dựa vào "Tọa độ" (Latitude, Longitude) và "Địa chỉ" trong Context để gom các địa điểm ở gần nhau vào cùng 1 buổi hoặc 1 ngày. Tránh việc bắt khách di chuyển quá xa giữa các bữa.
    3. CHỈ dùng dữ liệu trong Context. Context có dạng: [Loại - ID: X] Tên...
    4. Nếu chọn [Dining], BẮT BUỘC set activityType = 1, điền locationRestaurantId = X, và attractionId = null.
    5. Nếu chọn [Sightseeing], BẮT BUỘC set activityType = 2, điền attractionId = X, và locationRestaurantId = null.
    6. TUYỆT ĐỐI KHÔNG bọc kết quả trong markdown block (KHÔNG dùng ```json). Chỉ trả về chuỗi JSON thô.
    
    {format_instructions}"""),
    ("user", "Yêu cầu: {request}\n\nContext:\n{context}\n\nJSON:")
])
chain = prompt_template | llm | parser

modify_prompt_template = ChatPromptTemplate.from_messages([
    ("system", """Bạn là hệ thống sửa lịch trình CÓ CẢ ĂN UỐNG VÀ THAM QUAN.
    QUY TẮC BẮT BUỘC:
    1. Giữ nguyên JSON hiện tại nếu không phàn nàn.
    2. CHỈ thay thế các activity bị chê bằng dữ liệu lấy từ Context.
    3. Ưu tiên chọn địa điểm thay thế có Tọa độ (Latitude, Longitude) gần với các địa điểm khác trong cùng 1 buổi để tối ưu di chuyển.
    4. Nếu đổi sang [Dining] thì activityType=1, nếu đổi sang [Sightseeing] thì activityType=2. Các ID không dùng phải để null.
    5. TUYỆT ĐỐI KHÔNG bọc kết quả trong markdown block (KHÔNG dùng ```json). Chỉ trả về chuỗi JSON thô.
    
    {format_instructions}"""),
    ("user", "JSON hiện tại:\n{current_tour}\nYêu cầu sửa: {feedback}\nID bị chê: {rejected_ids}\nContext mới:\n{context}\nJSON:")
])
modify_chain = modify_prompt_template | llm | parser