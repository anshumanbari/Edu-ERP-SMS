from typing import List

from pydantic import BaseModel, ConfigDict


class CourseCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course: str
    count: int


class SemesterCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    semester: int
    count: int


class EnrollmentStatusCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    count: int


class StudentAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_students: int
    students_by_course: List[CourseCount]
    students_by_semester: List[SemesterCount]
    total_enrollments: int
    enrollments_by_status: List[EnrollmentStatusCount]
