from typing import List

from pydantic import BaseModel, Field, ConfigDict


class CourseBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        ..., min_length=2, max_length=100, description="Administrator-defined course name, e.g. 'Data Structures'"
    )
    code: str = Field(
        ..., min_length=2, max_length=20, description="Administrator-defined short code, e.g. 'CS201'"
    )
    semester_id: int = Field(..., gt=0, description="Primary key of the semester this course belongs to")
    credit_hours: int = Field(..., ge=1, le=20, description="Administrator-defined credit hours for the course")
    is_active: bool = Field(True, description="Whether the course is currently active and selectable")
    description: str | None = Field(None, max_length=255, description="Optional free-text notes")


class CourseCreate(CourseBase):
    pass


class CourseUpdate(CourseBase):
    pass


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    semester_id: int
    credit_hours: int
    is_active: bool
    description: str | None = None


class CourseDeleteResponse(BaseModel):
    message: str


class PaginatedCourseResponse(BaseModel):
    courses: List[CourseResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
