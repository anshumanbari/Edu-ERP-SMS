import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.program import (
    ProgramCreate,
    ProgramUpdate,
    ProgramResponse,
    ProgramDeleteResponse,
    PaginatedProgramResponse,
)
from app.crud import program as crud

router = APIRouter(
    prefix="/programs",
    tags=["Programs"],
)


# ---------------------------------------------------------------------------
# POST /programs/  — Create a new program
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=ProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new program",
)
def create_program(
    payload: ProgramCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> ProgramResponse:
    """
    Create a program record. Requires the **admin** role.

    - **name**: Administrator-defined program name (e.g. "B.Tech Computer Science") — must not already exist.
    - **code**: Administrator-defined short code (e.g. "BTCS") — must not already exist.
    - **department_id**: Primary key of the department this program belongs to.
    - **is_active**: Whether the program is active/selectable (default true).
    - **description**: Optional free-text notes.

    Raises **404 Not Found** if department_id does not reference an existing department.
    Raises **409 Conflict** if name or code is already registered.
    """
    return crud.create_program(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /programs/  — Retrieve all programs (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedProgramResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all programs (paginated)",
)
def get_all_programs(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(
        None, max_length=100, description="Search term matched against name, code, or description"
    ),
    department_id: int | None = Query(None, gt=0, description="Filter by exact department_id"),
    is_active: bool | None = Query(None, description="Filter by is_active flag"),
    sort_by: Literal["id", "name", "code"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
) -> PaginatedProgramResponse:
    """
    Return a paginated list of configured programs.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against name, code, or description.
    - **department_id**: Optional exact department filter.
    - **is_active**: Optional exact is_active filter.
    - **sort_by**: Optional field to sort by (id, name, code).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    programs, total_records = crud.get_paginated_programs(
        db=db,
        page=page,
        limit=limit,
        search=search,
        department_id=department_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedProgramResponse(
        programs=programs,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /programs/{program_id}  — Retrieve a single program
# ---------------------------------------------------------------------------
@router.get(
    "/{program_id}",
    response_model=ProgramResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a program by ID",
)
def get_program(
    program_id: int = Path(..., gt=0, description="Primary key of the program"),
    db: Session = Depends(get_db),
) -> ProgramResponse:
    """
    Fetch a single program by its primary key.

    Raises **404 Not Found** if no program with that ID exists.
    """
    program = crud.get_program_by_id(db=db, program_id=program_id)
    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program with ID {program_id} not found.",
        )
    return program


# ---------------------------------------------------------------------------
# PUT /programs/{program_id}  — Update a program
# ---------------------------------------------------------------------------
@router.put(
    "/{program_id}",
    response_model=ProgramResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a program by ID",
)
def update_program(
    payload: ProgramUpdate,
    program_id: int = Path(..., gt=0, description="Primary key of the program"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> ProgramResponse:
    """
    Update a program's details by its primary key. Requires the **admin** role.

    Also used to activate/deactivate a program by toggling **is_active**.

    Raises **404 Not Found** if no program with that ID exists, or if department_id
    does not reference an existing department.
    Raises **409 Conflict** if renaming to a name/code already in use.
    """
    program = crud.update_program(db=db, program_id=program_id, payload=payload)
    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program with ID {program_id} not found.",
        )
    return program


# ---------------------------------------------------------------------------
# DELETE /programs/{program_id}  — Delete a program
# ---------------------------------------------------------------------------
@router.delete(
    "/{program_id}",
    response_model=ProgramDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a program by ID",
)
def delete_program(
    program_id: int = Path(..., gt=0, description="Primary key of the program"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> ProgramDeleteResponse:
    """
    Permanently remove a program record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no program with that ID exists.
    Returns a success message on deletion.
    """
    program = crud.delete_program(db=db, program_id=program_id)
    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program with ID {program_id} not found.",
        )
    return ProgramDeleteResponse(
        message=f"Program with ID {program_id} deleted successfully."
    )
