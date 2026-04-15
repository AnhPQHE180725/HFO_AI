from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.config import llm
from app.schemas import TourResponse

parser = JsonOutputParser(pydantic_object=TourResponse)

prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Ban la he thong lap lich trinh du lich am thuc.
QUY TAC BAT BUOC:
1. Chi duoc dung ID co trong Context.
2. Dining phai set activityType=1, locationRestaurantId co gia tri, attractionId=null.
3. Sightseeing phai set activityType=2, attractionId co gia tri, locationRestaurantId=null.
4. startTime BAT BUOC dung dinh dang HH:MM:SS de parse duoc TimeSpan ben C#.
5. durationMinutes BAT BUOC co gia tri > 1 cho moi activity:
   - Dining: uoc tinh 45-90 phut tuy loai bua (sang nhanh ~45, trua/toi ~60-90).
   - Sightseeing: uoc tinh 60-180 phut tuy quy mo dia diem.
6. Lich trinh uu tien am thuc:
   - Mac dinh >=70% so activity la Dining.
   - Neu la lich 1 ngay thi co it nhat 3 bua (sang/trua/toi), uu tien them bua xe chieu neu hop ly.
7. Toi uu di chuyen:
   - Su dung toa do va khoang cach trong Context de di theo cum dia diem gan nhau.
   - Khong xep 2 diem qua xa lien tiep neu co lua chon gan hon.
   - Neu co "User location", activity dau ngay nen la diem gan nguoi dung hon.
8. Ton trong gio mo cua neu Context co Operating hours/Open-Close.
9. Uu tien da dang category mon an trong cung 1 ngay.
10. estimatedCost la tong uoc tinh tu cac diem Dining duoc chon.
11. Khong boc ket qua trong markdown. Chi tra ve JSON tho theo dung schema.

{format_instructions}""",
        ),
        (
            "user",
            "Yeu cau: {request}\n\nThong tin lap lich bo sung: {planning_hint}\n\nContext:\n{context}\n\nJSON:",
        ),
    ]
)
chain = prompt_template | llm | parser

modify_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Ban la he thong sua lich trinh du lich am thuc.
QUY TAC BAT BUOC:
1. Giu nguyen nhung activity khong bi phan nan.
2. Khong duoc chon lai bat ky ID nao nam trong danh sach bi loai.
3. Van phai dam bao uu tien am thuc (>=70% Dining) va toi uu di chuyen theo cum toa do.
4. Ton trong gio mo cua neu Context co.
5. Dung dung schema:
   - Dining: activityType=1, locationRestaurantId co gia tri, attractionId=null
   - Sightseeing: activityType=2, attractionId co gia tri, locationRestaurantId=null
6. startTime phai la HH:MM:SS.
7. durationMinutes BAT BUOC co gia tri > 1 cho moi activity:
   - Giu nguyen durationMinutes cua activity khong thay doi.
   - Activity moi: Dining ~45-90 phut, Sightseeing ~60-180 phut.
8. Cap nhat lai estimatedCost sau khi thay doi.
9. Khong boc markdown. Chi tra ve JSON tho.

{format_instructions}""",
        ),
        (
            "user",
            "Lich trinh hien tai:\n{current_tour}\n\nYeu cau sua: {feedback}\n\nThong tin lap lich bo sung: {planning_hint}\n\nDanh sach ID bi loai: {rejected_ids}\n\nContext thay the:\n{context}\n\nJSON:",
        ),
    ]
)
modify_chain = modify_prompt_template | llm | parser
