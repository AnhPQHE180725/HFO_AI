from pydantic import BaseModel, Field
from typing import List, Optional

class TourRequest(BaseModel):
    prompt: str = Field(..., example="Tour 1 ngày Hà Nội có cả ăn uống và tham quan")

class ActivityModel(BaseModel):
    activityType: int = Field(description="BẮT BUỘC: 1 nếu là Đi ăn (Dining), 2 nếu là Tham quan (Sightseeing)")
    locationRestaurantId: Optional[int] = Field(default=None, description="Mã ID quán ăn (Chỉ điền nếu activityType = 1, nếu không thì để null)")
    attractionId: Optional[int] = Field(default=None, description="Mã ID điểm tham quan (Chỉ điền nếu activityType = 2, nếu không thì để null)")
    startTime: str = Field(description="Thời gian bắt đầu (Ví dụ: '07:30:00')")
    note: str = Field(description="1 câu ngắn gọn lý do chọn")

class DayModel(BaseModel):
    dayNumber: int = Field(description="Số thứ tự của ngày")
    activities: List[ActivityModel] = Field(description="Danh sách hoạt động (kết hợp cả ăn uống và tham quan xen kẽ)")

class TourResponse(BaseModel):
    title: str = Field(description="Tiêu đề lịch trình do AI tự đặt")
    description: str = Field(description="Mô tả trải nghiệm")
    estimatedCost: float = Field(description="Tổng chi phí ước tính (Tính tổng giá các quán ăn và vé tham quan nếu có)")
    days: List[DayModel] = Field(description="Danh sách các ngày")

class ModifyTourRequest(BaseModel):
    current_tour: TourResponse = Field(description="Lịch trình hiện tại")
    feedback: str = Field(description="Khách muốn sửa gì?")
    rejected_restaurant_ids: List[int] = Field(default=[], description="Danh sách ID quán ăn bị chê")
    rejected_attraction_ids: List[int] = Field(default=[], description="Danh sách ID điểm tham quan bị chê")