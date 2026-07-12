import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.classroom import (
    ClassroomCreate,
    ClassroomUpdate,
    ClassroomResponse,
    ClassroomDeleteResponse,
    PaginatedClassroomResponse,
)
from app.crud import classroom as crud

router = APIRouter(
    prefix="/classrooms",
    tags=["Classrooms"],
)


# ---------------------------------------------------------------------------
# POST /classrooms/  — Create a new classroom
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=ClassroomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new classroom",
)
def create_classroom(
    payload: ClassroomCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> ClassroomResponse:
    """
    Create a classroom record. Requires the **admin** role.

    - **room_number**: Administrator-defined room number (e.g. "B-204"), unique within its building.
    - **building**: Optional building/block name.
    - **capacity**: Maximum number of students the room can seat.
    - **is_active**: Whether the classroom is active/bookable (default true).
    - **description**: Optional free-text notes.

    Raises **409 Conflict** if the room_number is already used within the same building.
    """
    return crud.create_classroom(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /classrooms/  — Retrieve all classrooms (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedClassroomResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all classrooms (paginated)",
)
def get_all_classrooms(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(
        None, max_length=100, description="Search term matched against room_number, building, or description"
    ),
    is_active: bool | None = Query(None, description="Filter by is_active flag"),
    sort_by: Literal["id", "room_number", "capacity"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
) -> PaginatedClassroomResponse:
    """
    Return a paginated list of configured classrooms.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against room_number, building, or description.
    - **is_active**: Optional exact is_active filter.
    - **sort_by**: Optional field to sort by (id, room_number, capacity).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    classrooms, total_records = crud.get_paginated_classrooms(
        db=db,
        page=page,
        limit=limit,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedClassroomResponse(
        classrooms=classrooms,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /classrooms/{classroom_id}  — Retrieve a single classroom
# ---------------------------------------------------------------------------
@router.get(
    "/{classroom_id}",
    response_model=ClassroomResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a classroom by ID",
)
def get_classroom(
    classroom_id: int = Path(..., gt=0, description="Primary key of the classroom"),
    db: Session = Depends(get_db),
) -> ClassroomResponse:
    """
    Fetch a single classroom by its primary key.

    Raises **404 Not Found** if no classroom with that ID exists.
    """
    classroom = crud.get_classroom_by_id(db=db, classroom_id=classroom_id)
    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Classroom with ID {classroom_id} not found.",
        )
    return classroom


# ---------------------------------------------------------------------------
# PUT /classrooms/{classroom_id}  — Update a classroom
# ---------------------------------------------------------------------------
@router.put(
    "/{classroom_id}",
    response_model=ClassroomResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a classroom by ID",
)
def update_classroom(
    payload: ClassroomUpdate,
    classroom_id: int = Path(..., gt=0, description="Primary key of the classroom"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> ClassroomResponse:
    """
    Update a classroom's details by its primary key. Requires the **admin** role.

    Also used to activate/deactivate a classroom by toggling **is_active**.

    Raises **404 Not Found** if no classroom with that ID exists.
    Raises **409 Conflict** if the new room_number is already used within the target building.
    """
    classroom = crud.update_classroom(db=db, classroom_id=classroom_id, payload=payload)
    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Classroom with ID {classroom_id} not found.",
        )
    return classroom


# ---------------------------------------------------------------------------
# DELETE /classrooms/{classroom_id}  — Delete a classroom
# ---------------------------------------------------------------------------
@router.delete(
    "/{classroom_id}",
    response_model=ClassroomDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a classroom by ID",
)
def delete_classroom(
    classroom_id: int = Path(..., gt=0, description="Primary key of the classroom"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> ClassroomDeleteResponse:
    """
    Permanently remove a classroom record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no classroom with that ID exists.
    Returns a success message on deletion.
    """
    classroom = crud.delete_classroom(db=db, classroom_id=classroom_id)
    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Classroom with ID {classroom_id} not found.",
        )
    return ClassroomDeleteResponse(
        message=f"Classroom with ID {classroom_id} deleted successfully."
    )
