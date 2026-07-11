from datetime import date
from typing import List, Literal

from pydantic import BaseModel, Field, ConfigDict


class AttendanceBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    student_id: int = Field(..., gt=0, description="Primary key of the student this record belongs to")
    subject_id: int = Field(..., gt=0, description="Primary key of the subject this record belongs to")
    academic_session_id: int = Field(
        ..., gt=0, description="Primary key of the academic session this record belongs to"
    )
    attendance_date: date = Field(..., description="Calendar date the attendance was taken")
    status: Literal["present", "absent", "late", "excused"] = Field(
        ..., description="Attendance status recorded by the teacher/administrator"
    )
    remarks: str | None = Field(None, max_length=255, description="Optional free-text notes")


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(AttendanceBase):
    pass


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    subject_id: int
    academic_session_id: int
    attendance_date: date
    status: str
    marked_by_id: int
    remarks: str | None = None


class AttendanceDeleteResponse(BaseModel):
    message: str


class PaginatedAttendanceResponse(BaseModel):
    attendance_records: List[AttendanceResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
