from pydantic import BaseModel, ConfigDict


class TeacherAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_teachers: int
    total_active_assignments: int
    distinct_assigned_teachers: int
