import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.fee_payment import (
    FeePaymentCreate,
    FeePaymentUpdate,
    FeePaymentResponse,
    FeePaymentDeleteResponse,
    PaginatedFeePaymentResponse,
)
from app.crud import fee_payment as crud

router = APIRouter(
    prefix="/fee-payments",
    tags=["Fee Payments"],
)


# ---------------------------------------------------------------------------
# POST /fee-payments/  — Record a student's fee payment
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=FeePaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a student's fee payment",
)
def create_fee_payment(
    payload: FeePaymentCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> FeePaymentResponse:
    """
    Record a student's payment against a fee structure. Requires the **admin** role.

    - **student_id**, **fee_structure_id**: Must reference existing records.
    - **amount_paid**: Cumulative amount paid so far (must not exceed the fee's amount).
    - **payment_date**: Date of the latest payment (ignored if amount_paid is 0).
    - **remarks**: Optional free-text notes.

    The response's **status** field ("paid", "pending", or "overdue") is computed
    automatically from amount_paid versus the fee's amount and due_date.

    Raises **404 Not Found** if student_id or fee_structure_id does not reference an existing record.
    Raises **400 Bad Request** if amount_paid exceeds the fee structure's amount.
    Raises **409 Conflict** if the student already has a payment record for this fee structure.
    """
    return crud.create_fee_payment(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /fee-payments/  — Retrieve fee payments (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedFeePaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve fee payments (paginated)",
)
def get_all_fee_payments(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(None, max_length=100, description="Search term matched against remarks"),
    student_id: int | None = Query(None, gt=0, description="Filter by exact student_id"),
    fee_structure_id: int | None = Query(None, gt=0, description="Filter by exact fee_structure_id"),
    status_filter: Literal["paid", "pending", "overdue"] | None = Query(
        None, alias="status", description="Filter by computed payment status"
    ),
    sort_by: Literal["id", "amount_paid", "payment_date"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> PaginatedFeePaymentResponse:
    """
    Return a paginated list of fee payments. Requires the **admin** role.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against remarks.
    - **student_id** / **fee_structure_id**: Optional exact filters.
    - **status**: Optional filter by computed status ("paid", "pending", "overdue").
    - **sort_by**: Optional field to sort by (id, amount_paid, payment_date).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    fee_payments, total_records = crud.get_paginated_fee_payments(
        db=db,
        page=page,
        limit=limit,
        search=search,
        student_id=student_id,
        fee_structure_id=fee_structure_id,
        status_filter=status_filter,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedFeePaymentResponse(
        fee_payments=fee_payments,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /fee-payments/{fee_payment_id}  — Retrieve a single fee payment
# ---------------------------------------------------------------------------
@router.get(
    "/{fee_payment_id}",
    response_model=FeePaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a fee payment by ID",
)
def get_fee_payment(
    fee_payment_id: int = Path(..., gt=0, description="Primary key of the fee payment"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> FeePaymentResponse:
    """
    Fetch a single fee payment by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no fee payment with that ID exists.
    """
    fee_payment = crud.get_fee_payment_by_id(db=db, fee_payment_id=fee_payment_id)
    if fee_payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee payment with ID {fee_payment_id} not found.",
        )
    return fee_payment


# ---------------------------------------------------------------------------
# PUT /fee-payments/{fee_payment_id}  — Update a fee payment
# ---------------------------------------------------------------------------
@router.put(
    "/{fee_payment_id}",
    response_model=FeePaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a fee payment by ID",
)
def update_fee_payment(
    payload: FeePaymentUpdate,
    fee_payment_id: int = Path(..., gt=0, description="Primary key of the fee payment"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> FeePaymentResponse:
    """
    Update a fee payment by its primary key (e.g. to record an additional
    installment). Requires the **admin** role.

    Raises **404 Not Found** if no fee payment with that ID exists, or if
    student_id/fee_structure_id does not reference an existing record.
    Raises **400 Bad Request** if amount_paid exceeds the fee structure's amount.
    Raises **409 Conflict** if the change collides with an existing payment for the
    same student+fee structure.
    """
    fee_payment = crud.update_fee_payment(db=db, fee_payment_id=fee_payment_id, payload=payload)
    if fee_payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee payment with ID {fee_payment_id} not found.",
        )
    return fee_payment


# ---------------------------------------------------------------------------
# DELETE /fee-payments/{fee_payment_id}  — Delete a fee payment
# ---------------------------------------------------------------------------
@router.delete(
    "/{fee_payment_id}",
    response_model=FeePaymentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a fee payment by ID",
)
def delete_fee_payment(
    fee_payment_id: int = Path(..., gt=0, description="Primary key of the fee payment"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> FeePaymentDeleteResponse:
    """
    Permanently remove a fee payment record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no fee payment with that ID exists.
    Returns a success message on deletion.
    """
    fee_payment = crud.delete_fee_payment(db=db, fee_payment_id=fee_payment_id)
    if fee_payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee payment with ID {fee_payment_id} not found.",
        )
    return FeePaymentDeleteResponse(
        message=f"Fee payment with ID {fee_payment_id} deleted successfully."
    )
