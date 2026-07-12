from typing import List

from pydantic import BaseModel, Field, ConfigDict


class TeacherAssignmentBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    teacher_id: int = Field(..., gt=0, description="Primary key of the teacher being assigned")
    subject_id: int = Field(..., gt=0, description="Primary key of the subject to assign the teacher to")
    section_id: int = Field(..., gt=0, description="Primary key of the section to assign the teacher to")
    academic_session_id: int = Field(
        ..., gt=0, description="Primary key of the academic session this assignment applies to"
    )
    is_active: bool = Field(True, description="Whether the assignment is currently active/in effect")
    remarks: str | None = Field(None, max_length=255, description="Optional free-text notes")


class TeacherAssignmentCreate(TeacherAssignmentBase):
    pass


class TeacherAssignmentUpdate(TeacherAssignmentBase):
    pass


class TeacherAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    teacher_id: int
    subject_id: int
    section_id: int
    academic_session_id: int
    is_active: bool
    remarks: str | None = None


class TeacherAssignmentDeleteResponse(BaseModel):
    message: str


class PaginatedTeacherAssignmentResponse(BaseModel):
    teacher_assignments: List[TeacherAssignmentResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
