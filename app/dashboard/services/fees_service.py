from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.dashboard.schemas.fees import FeePaymentStatusCount, FeesAnalyticsResponse
from app.models.fee_payment import FeePayment
from app.models.fee_structure import FeeStructure


def get_fees_analytics(db: Session) -> FeesAnalyticsResponse:
    """
    Fee structure and collection totals. Payment status is computed the same
    way the Fees module itself derives it (paid/overdue/pending from
    amount_paid vs. amount and due_date) so the dashboard never disagrees
    with the Fees module's own view of a payment's state.
    """
    total_fee_structures = db.query(func.count(FeeStructure.id)).scalar() or 0
    total_amount_due = db.query(func.sum(FeeStructure.amount)).scalar() or 0.0
    total_amount_collected = db.query(func.sum(FeePayment.amount_paid)).scalar() or 0.0

    status_expr = case(
        (FeePayment.amount_paid >= FeeStructure.amount, "paid"),
        (FeeStructure.due_date < func.current_date(), "overdue"),
        else_="pending",
    )
    status_rows = (
        db.query(status_expr.label("status"), func.count(FeePayment.id))
        .join(FeeStructure, FeePayment.fee_structure_id == FeeStructure.id)
        .group_by(status_expr)
        .all()
    )
    payments_by_status = [
        FeePaymentStatusCount(status=status, count=count) for status, count in status_rows
    ]

    return FeesAnalyticsResponse(
        total_fee_structures=total_fee_structures,
        total_amount_due=total_amount_due,
        total_amount_collected=total_amount_collected,
        payments_by_status=payments_by_status,
    )
