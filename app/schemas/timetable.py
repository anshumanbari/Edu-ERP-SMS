from datetime import time
from typing import List, Literal

from pydantic import BaseModel, Field, ConfigDict, model_validator


class TimetableBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    section_id: int = Field(..., gt=0, description="Primary key of the section this class period belongs to")
    subject_id: int = Field(..., gt=0, description="Primary key of the subject being taught")
    teacher_id: int = Field(..., gt=0, description="Primary key of the teacher taking the class")
    classroom_id: int = Field(..., gt=0, description="Primary key of the classroom the class is held in")
    academic_session_id: int = Field(
        ..., gt=0, description="Primary key of the academic session this schedule entry belongs to"
    )
    day_of_week: Literal[
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
    ] = Field(..., description="Day of the week this class period recurs on")
    start_time: time = Field(..., description="Time the class period starts")
    end_time: time = Field(..., description="Time the class period ends")
    is_active: bool = Field(True, description="Whether this schedule entry is currently active")
    remarks: str | None = Field(None, max_length=255, description="Optional free-text notes")

    @model_validator(mode="after")
    def _validate_time_range(self) -> "TimetableBase":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be later than start_time.")
        return self


class TimetableCreate(TimetableBase):
    pass


class TimetableUpdate(TimetableBase):
    pass


class TimetableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    section_id: int
    subject_id: int
    teacher_id: int
    classroom_id: int
    academic_session_id: int
    day_of_week: str
    start_time: time
    end_time: time
    is_active: bool
    remarks: str | None = None


class TimetableDeleteResponse(BaseModel):
    message: str


class PaginatedTimetableResponse(BaseModel):
    timetables: List[TimetableResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
