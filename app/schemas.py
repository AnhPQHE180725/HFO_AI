from pydantic import BaseModel, Field
from typing import List

class TourRequest(BaseModel):
    prompt: str = Field(..., example="Tôi muốn lịch trình 1 ngày ngon bổ rẻ ở phố cổ")

class ActivityModel(BaseModel):
    locationRestaurantId: int = Field(description="Mã ID quán ăn (Lấy từ [ID: X])")
    startTime: str = Field(description="Thời gian bắt đầu (Ví dụ: '07:30:00')")
    note: str = Field(description="1 câu ngắn gọn lý do chọn")

class DayModel(BaseModel):
    dayNumber: int = Field(description="Số thứ tự của ngày")
    activities: List[ActivityModel] = Field(description="Danh sách hoạt động")

class TourResponse(BaseModel):
    title: str = Field(description="Tiêu đề lịch trình do AI tự đặt")
    description: str = Field(description="Mô tả trải nghiệm")
    estimatedCost: float = Field(description="Tổng chi phí ước tính")
    days: List[DayModel] = Field(description="Danh sách các ngày")

class ModifyTourRequest(BaseModel):
    current_tour: TourResponse = Field(description="Lịch trình hiện tại")
    feedback: str = Field(description="Khách muốn sửa gì?")
    rejected_ids: List[int] = Field(default=[], description="Danh sách ID quán bị chê")