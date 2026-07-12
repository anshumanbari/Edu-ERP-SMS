from typing import List

from pydantic import BaseModel, Field, ConfigDict


class ClassroomBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    room_number: str = Field(
        ..., min_length=1, max_length=20, description="Administrator-defined room number, e.g. 'B-204'"
    )
    building: str | None = Field(None, max_length=100, description="Optional building/block name")
    capacity: int = Field(..., gt=0, description="Maximum number of students the room can seat")
    is_active: bool = Field(True, description="Whether the classroom is currently active and bookable")
    description: str | None = Field(None, max_length=255, description="Optional free-text notes")


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomUpdate(ClassroomBase):
    pass


class ClassroomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_number: str
    building: str | None = None
    capacity: int
    is_active: bool
    description: str | None = None


class ClassroomDeleteResponse(BaseModel):
    message: str


class PaginatedClassroomResponse(BaseModel):
    classrooms: List[ClassroomResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
