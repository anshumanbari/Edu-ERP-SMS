from typing import List

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class TeacherBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., min_length=1, max_length=100, description="The full name of the teacher")
    email: EmailStr = Field(..., max_length=100, description="The unique email address of the teacher")
    phone: int = Field(
        ...,
        ge=1000000,
        le=999999999999999,
        description="The contact phone number of the teacher (digits only, 7-15 digits)",
    )
    subject: str = Field(..., min_length=1, max_length=100, description="The subject taught by the teacher")
    experience_years: int = Field(..., ge=0, le=60, description="Years of teaching experience")


class TeacherCreate(TeacherBase):
    pass


class TeacherUpdate(TeacherBase):
    pass


class TeacherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: int
    subject: str
    experience_years: int


class TeacherDeleteResponse(BaseModel):
    message: str


class PaginatedTeacherResponse(BaseModel):
    teachers: List[TeacherResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
