from typing import List

from pydantic import BaseModel, ConfigDict


class AttendanceStatusCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    count: int


class AttendanceAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_records: int
    attendance_by_status: List[AttendanceStatusCount]
    overall_attendance_percentage: float | None = None
