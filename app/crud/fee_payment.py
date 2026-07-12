from fastapi import HTTPException, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.fee_payment import FeePayment
from app.models.fee_structure import FeeStructure
from app.models.student import Student
from app.schemas.fee_payment import FeePaymentCreate, FeePaymentResponse, FeePaymentUpdate


def _status_expression():
    """
    Payment status is computed on the fly rather than stored, so that a
    "pending" payment correctly becomes "overdue" purely with the passage of
    time, without requiring a write.
    """
    return case(
        (FeePayment.amount_paid >= FeeStructure.amount, "paid"),
        (FeeStructure.due_date < func.current_date(), "overdue"),
        else_="pending",
    )


def _to_response(payment: FeePayment, status_value: str) -> FeePaymentResponse:
    return FeePaymentResponse(
        id=payment.id,
        student_id=payment.student_id,
        fee_structure_id=payment.fee_structure_id,
        amount_paid=payment.amount_paid,
        payment_date=payment.payment_date,
        status=status_value,
        remarks=payment.remarks,
    )


def _get_fee_structure_or_404(db: Session, fee_structure_id: int) -> FeeStructure:
    fee_structure = db.query(FeeStructure).filter(FeeStructure.id == fee_structure_id).first()
    if fee_structure is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee structure with ID {fee_structure_id} not found.",
        )
    return fee_structure


def _check_student_exists(db: Session, student_id: int) -> None:
    if db.query(Student).filter(Student.id == student_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )


def _check_amount_within_range(amount_paid: float, fee_structure: FeeStructure) -> None:
    if amount_paid > fee_structure.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"amount_paid ({amount_paid}) cannot exceed the fee amount ({fee_structure.amount}).",
        )


def _check_duplicate(
    db: Session,
    student_id: int,
    fee_structure_id: int,
    exclude_id: int | None = None,
) -> None:
    """
    A student can only have one payment record per fee structure.
    """
    query = db.query(FeePayment).filter(
        FeePayment.student_id == student_id,
        FeePayment.fee_structure_id == fee_structure_id,
    )
    if exclude_id is not None:
        query = query.filter(FeePayment.id != exclude_id)

    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Student {student_id} already has a payment record for fee structure {fee_structure_id}."
            ),
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_fee_payment(db: Session, payload: FeePaymentCreate) -> FeePaymentResponse:
    """
    Insert a new fee payment record into the database.

    Raises:
        HTTPException 404: If student_id or fee_structure_id does not reference an
                            existing record.
        HTTPException 400: If amount_paid exceeds the fee structure's amount.
        HTTPException 409: If the student already has a payment record for this
                            fee structure.

    Returns:
        The newly created payment, with its computed status.
    """
    fee_structure = _get_fee_structure_or_404(db, payload.fee_structure_id)
    _check_student_exists(db, payload.student_id)
    _check_amount_within_range(payload.amount_paid, fee_structure)
    _check_duplicate(db, student_id=payload.student_id, fee_structure_id=payload.fee_structure_id)

    payment_date = payload.payment_date if payload.amount_paid > 0 else None

    payment = FeePayment(
        student_id=payload.student_id,
        fee_structure_id=payload.fee_structure_id,
        amount_paid=payload.amount_paid,
        payment_date=payment_date,
        remarks=payload.remarks,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return get_fee_payment_by_id(db, payment.id)


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_fee_payments(db: Session) -> list[FeePaymentResponse]:
    rows = (
        db.query(FeePayment, _status_expression().label("status"))
        .join(FeeStructure, FeePayment.fee_structure_id == FeeStructure.id)
        .all()
    )
    return [_to_response(payment, status_value) for payment, status_value in rows]


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_fee_payments(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    student_id: int | None = None,
    fee_structure_id: int | None = None,
    status_filter: str | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[FeePaymentResponse], int]:
    """
    Retrieve a page of fee payments along with the total record count.

    Args:
        db:               Active SQLAlchemy session (injected via Depends).
        page:             1-indexed page number.
        limit:            Maximum number of records to return for the page.
        search:           Optional case-insensitive substring to match against remarks.
        student_id:       Optional exact student_id to filter by.
        fee_structure_id: Optional exact fee_structure_id to filter by.
        status_filter:    Optional exact computed status to filter by
                          ("paid", "pending", or "overdue").
        sort_by:          Optional field to sort by (id, amount_paid, payment_date).
        sort_order:       "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (fee payments on the requested page, total number of records).
    """
    status_expr = _status_expression()
    query = db.query(FeePayment, status_expr.label("status")).join(
        FeeStructure, FeePayment.fee_structure_id == FeeStructure.id
    )

    if search:
        pattern = f"%{search}%"
        query = query.filter(FeePayment.remarks.ilike(pattern))

    if student_id is not None:
        query = query.filter(FeePayment.student_id == student_id)

    if fee_structure_id is not None:
        query = query.filter(FeePayment.fee_structure_id == fee_structure_id)

    if status_filter:
        query = query.filter(status_expr == status_filter)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(FeePayment, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    rows = query.offset(offset).limit(limit).all()
    payments = [_to_response(payment, status_value) for payment, status_value in rows]
    return payments, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_fee_payment_by_id(db: Session, fee_payment_id: int) -> FeePaymentResponse | None:
    row = (
        db.query(FeePayment, _status_expression().label("status"))
        .join(FeeStructure, FeePayment.fee_structure_id == FeeStructure.id)
        .filter(FeePayment.id == fee_payment_id)
        .first()
    )
    if row is None:
        return None
    payment, status_value = row
    return _to_response(payment, status_value)


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_fee_payment(
    db: Session, fee_payment_id: int, payload: FeePaymentUpdate
) -> FeePaymentResponse | None:
    payment = db.query(FeePayment).filter(FeePayment.id == fee_payment_id).first()
    if payment is None:
        return None

    fee_structure = _get_fee_structure_or_404(db, payload.fee_structure_id)

    references_changed = (
        payload.student_id != payment.student_id
        or payload.fee_structure_id != payment.fee_structure_id
    )
    if references_changed:
        _check_student_exists(db, payload.student_id)
        _check_duplicate(
            db,
            student_id=payload.student_id,
            fee_structure_id=payload.fee_structure_id,
            exclude_id=fee_payment_id,
        )

    _check_amount_within_range(payload.amount_paid, fee_structure)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)
    if payment.amount_paid == 0:
        payment.payment_date = None

    db.commit()
    db.refresh(payment)
    return get_fee_payment_by_id(db, fee_payment_id)


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_fee_payment(db: Session, fee_payment_id: int) -> FeePayment | None:
    payment = db.query(FeePayment).filter(FeePayment.id == fee_payment_id).first()
    if payment is None:
        return None

    db.delete(payment)
    db.commit()
    return payment
