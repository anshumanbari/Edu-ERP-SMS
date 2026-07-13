from pydantic import BaseModel, ConfigDict


class AcademicAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_departments: int
    total_programs: int
    total_semesters: int
    total_courses: int
    total_subjects: int
    total_sections: int
    total_academic_sessions: int
    current_academic_session: str | None = None
