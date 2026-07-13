from typing import List

from pydantic import BaseModel, ConfigDict


class ResultStatusCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    count: int


class ExaminationAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_examinations: int
    total_exam_marks_recorded: int
    average_result_percentage: float | None = None
    results_by_status: List[ResultStatusCount]
    total_results_published: int
