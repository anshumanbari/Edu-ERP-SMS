import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.fee_structure import (
    FeeStructureCreate,
    FeeStructureUpdate,
    FeeStructureResponse,
    FeeStructureDeleteResponse,
    PaginatedFeeStructureResponse,
)
from app.crud import fee_structure as crud

router = APIRouter(
    prefix="/fee-structures",
    tags=["Fee Structures"],
)


# ---------------------------------------------------------------------------
# POST /fee-structures/  — Create a new fee structure
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=FeeStructureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new fee structure",
)
def create_fee_structure(
    payload: FeeStructureCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> FeeStructureResponse:
    """
    Create a fee structure record. Requires the **admin** role.

    - **name**: Administrator-defined fee name (e.g. "Tuition Fee"), unique within
      its program+semester+academic session.
    - **program_id**: Primary key of the program this fee applies to.
    - **semester_id**: Primary key of the semester this fee applies to (must belong to program_id).
    - **academic_session_id**: Primary key of the academic session this fee applies to.
    - **amount**: Amount due.
    - **due_date**: Calendar date payment is due by.
    - **is_active**: Whether this fee structure is active (default true).
    - **description**: Optional free-text notes.

    Raises **404 Not Found** if program_id, semester_id, or academic_session_id does not exist.
    Raises **400 Bad Request** if semester_id does not belong to program_id.
    Raises **409 Conflict** if the name is already used within the same program+semester+session.
    """
    return crud.create_fee_structure(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /fee-structures/  — Retrieve all fee structures (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedFeeStructureResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all fee structures (paginated)",
)
def get_all_fee_structures(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(
        None, max_length=100, description="Search term matched against name or description"
    ),
    program_id: int | None = Query(None, gt=0, description="Filter by exact program_id"),
    semester_id: int | None = Query(None, gt=0, description="Filter by exact semester_id"),
    academic_session_id: int | None = Query(None, gt=0, description="Filter by exact academic_session_id"),
    is_active: bool | None = Query(None, description="Filter by is_active flag"),
    sort_by: Literal["id", "name", "amount", "due_date"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
) -> PaginatedFeeStructureResponse:
    """
    Return a paginated list of configured fee structures.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against name or description.
    - **program_id** / **semester_id** / **academic_session_id**: Optional exact filters.
    - **is_active**: Optional exact is_active filter.
    - **sort_by**: Optional field to sort by (id, name, amount, due_date).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    fee_structures, total_records = crud.get_paginated_fee_structures(
        db=db,
        page=page,
        limit=limit,
        search=search,
        program_id=program_id,
        semester_id=semester_id,
        academic_session_id=academic_session_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedFeeStructureResponse(
        fee_structures=fee_structures,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /fee-structures/{fee_structure_id}  — Retrieve a single fee structure
# ---------------------------------------------------------------------------
@router.get(
    "/{fee_structure_id}",
    response_model=FeeStructureResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a fee structure by ID",
)
def get_fee_structure(
    fee_structure_id: int = Path(..., gt=0, description="Primary key of the fee structure"),
    db: Session = Depends(get_db),
) -> FeeStructureResponse:
    """
    Fetch a single fee structure by its primary key.

    Raises **404 Not Found** if no fee structure with that ID exists.
    """
    fee_structure = crud.get_fee_structure_by_id(db=db, fee_structure_id=fee_structure_id)
    if fee_structure is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee structure with ID {fee_structure_id} not found.",
        )
    return fee_structure


# ---------------------------------------------------------------------------
# PUT /fee-structures/{fee_structure_id}  — Update a fee structure
# ---------------------------------------------------------------------------
@router.put(
    "/{fee_structure_id}",
    response_model=FeeStructureResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a fee structure by ID",
)
def update_fee_structure(
    payload: FeeStructureUpdate,
    fee_structure_id: int = Path(..., gt=0, description="Primary key of the fee structure"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> FeeStructureResponse:
    """
    Update a fee structure's details by its primary key. Requires the **admin** role.

    Also used to activate/deactivate a fee structure by toggling **is_active**.

    Raises **404 Not Found** if no fee structure with that ID exists, or if
    program_id/semester_id/academic_session_id does not reference an existing record.
    Raises **400 Bad Request** if semester_id does not belong to program_id.
    Raises **409 Conflict** if the new name is already used within the target program+semester+session.
    """
    fee_structure = crud.update_fee_structure(db=db, fee_structure_id=fee_structure_id, payload=payload)
    if fee_structure is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee structure with ID {fee_structure_id} not found.",
        )
    return fee_structure


# ---------------------------------------------------------------------------
# DELETE /fee-structures/{fee_structure_id}  — Delete a fee structure
# ---------------------------------------------------------------------------
@router.delete(
    "/{fee_structure_id}",
    response_model=FeeStructureDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a fee structure by ID",
)
def delete_fee_structure(
    fee_structure_id: int = Path(..., gt=0, description="Primary key of the fee structure"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> FeeStructureDeleteResponse:
    """
    Permanently remove a fee structure record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no fee structure with that ID exists.
    Returns a success message on deletion.
    """
    fee_structure = crud.delete_fee_structure(db=db, fee_structure_id=fee_structure_id)
    if fee_structure is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fee structure with ID {fee_structure_id} not found.",
        )
    return FeeStructureDeleteResponse(
        message=f"Fee structure with ID {fee_structure_id} deleted successfully."
    )
