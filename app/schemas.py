from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class TourRequest(BaseModel):
    prompt: str = Field(..., example="Tour 1 ngay Ha Noi co ca an uong va tham quan")
    userLatitude: Optional[float] = Field(
        default=None,
        description="Vi do hien tai cua nguoi dung (optional), de toi uu route theo khoang cach.",
    )
    userLongitude: Optional[float] = Field(
        default=None,
        description="Kinh do hien tai cua nguoi dung (optional), de toi uu route theo khoang cach.",
    )


class ActivityModel(BaseModel):
    activityType: int = Field(description="1 = Dining, 2 = Sightseeing.")
    locationRestaurantId: Optional[int] = Field(
        default=None, description="Chi co gia tri khi activityType = 1."
    )
    attractionId: Optional[int] = Field(
        default=None, description="Chi co gia tri khi activityType = 2."
    )
    startTime: str = Field(description="Dinh dang HH:MM:SS, vi du 07:30:00.")
    note: str = Field(description="Ghi chu ngan gon cho activity.")


class DayModel(BaseModel):
    dayNumber: int = Field(description="So thu tu ngay.")
    activities: List[ActivityModel] = Field(description="Danh sach activities trong ngay.")


class TourResponse(BaseModel):
    title: str = Field(description="Tieu de lich trinh.")
    description: str = Field(description="Mo ta tong quan.")
    estimatedCost: float = Field(description="Tong chi phi uoc tinh.")
    days: List[DayModel] = Field(description="Danh sach cac ngay.")


class ModifyTourRequest(BaseModel):
    current_tour: TourResponse = Field(description="Lich trinh hien tai.")
    feedback: str = Field(description="Yeu cau dieu chinh.")

    # Backward compatible with FE currently sending rejected_ids.
    rejected_ids: List[int] = Field(default_factory=list)

    # New optional split lists by place type.
    rejected_restaurant_ids: List[int] = Field(default_factory=list)
    rejected_attraction_ids: List[int] = Field(default_factory=list)

    userLatitude: Optional[float] = Field(default=None)
    userLongitude: Optional[float] = Field(default=None)

    @model_validator(mode="after")
    def _merge_legacy_rejected_ids(self):
        if self.rejected_ids:
            legacy_ids = set(self.rejected_ids)
            self.rejected_restaurant_ids = sorted(
                set(self.rejected_restaurant_ids).union(legacy_ids)
            )
            self.rejected_attraction_ids = sorted(
                set(self.rejected_attraction_ids).union(legacy_ids)
            )
        return self
