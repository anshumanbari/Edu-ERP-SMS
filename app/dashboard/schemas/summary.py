from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DashboardSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_students: int
    total_teachers: int
    total_active_enrollments: int
    total_examinations: int
    total_fee_structures: int
    generated_at: datetime
