from typing import List

from pydantic import BaseModel, ConfigDict


class FeePaymentStatusCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    count: int


class FeesAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_fee_structures: int
    total_amount_due: float
    total_amount_collected: float
    payments_by_status: List[FeePaymentStatusCount]
