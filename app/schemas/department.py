from typing import List

from pydantic import BaseModel, Field, ConfigDict


class DepartmentBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        ..., min_length=2, max_length=100, description="Administrator-defined department name, e.g. 'Computer Science'"
    )
    code: str = Field(
        ..., min_length=2, max_length=20, description="Administrator-defined short code, e.g. 'CSE'"
    )
    is_active: bool = Field(True, description="Whether the department is currently active and selectable")
    description: str | None = Field(None, max_length=255, description="Optional free-text notes")


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(DepartmentBase):
    pass


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    is_active: bool
    description: str | None = None


class DepartmentDeleteResponse(BaseModel):
    message: str


class PaginatedDepartmentResponse(BaseModel):
    departments: List[DepartmentResponse]
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
