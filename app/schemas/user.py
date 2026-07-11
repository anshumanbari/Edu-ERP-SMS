import re
from typing import Literal

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator

from app.core.roles import Role


class UserBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., min_length=1, max_length=100, description="The full name of the user")
    email: EmailStr = Field(..., max_length=100, description="The unique email address of the user")


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="The account password (min 8 characters, at least one letter and one digit)",
    )
    role: Literal[Role.STUDENT, Role.TEACHER] = Field(
        default=Role.STUDENT,
        description="Account role. Self-registration is limited to 'student' or 'teacher' — "
        "'admin' accounts must be provisioned separately.",
    )

    @field_validator("password")
    @classmethod
    def password_must_be_reasonably_strong(cls, value: str) -> str:
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("Password must contain at least one letter and one digit.")
        return value


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: Role
