from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.schemas import TourResponse
from app.config import llm

parser = JsonOutputParser(pydantic_object=TourResponse)

# Prompt tạo mới
prompt_template = ChatPromptTemplate.from_messages([
    ("system", """Bạn là hệ thống API thiết kế lịch trình tự động của HFO. QUY TẮC:
    1. CHỈ dùng quán ăn trong Context. Định dạng: [ID: X] Tên quán...
    2. Trả về đúng 'locationRestaurantId' tương ứng.
    3. Trả về JSON, không giải thích thêm:
    {format_instructions}"""),
    ("user", "Yêu cầu: {request}\n\nContext:\n{context}\n\nJSON:")
])
chain = prompt_template | llm | parser

# Prompt chỉnh sửa
modify_prompt_template = ChatPromptTemplate.from_messages([
    ("system", """Bạn là hệ thống API chỉnh sửa lịch trình HFO. QUY TẮC:
    1. Giữ nguyên JSON hiện tại nếu không phàn nàn.
    2. CHỈ thay thế 'locationRestaurantId' ở chỗ khách muốn đổi bằng quán lấy từ Context.
    3. KHÔNG chọn quán nằm trong Danh sách ID bị chê.
    4. Trả về JSON, không giải thích:
    {format_instructions}"""),
    ("user", "JSON hiện tại:\n{current_tour}\nYêu cầu sửa: {feedback}\nID bị chê: {rejected_ids}\nContext mới:\n{context}\nJSON:")
])
modify_chain = modify_prompt_template | llm | parser