import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.roles import Role
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentDeleteResponse,
    PaginatedDepartmentResponse,
)
from app.crud import department as crud

router = APIRouter(
    prefix="/departments",
    tags=["Departments"],
)


# ---------------------------------------------------------------------------
# POST /departments/  — Create a new department
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new department",
)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> DepartmentResponse:
    """
    Create a department record. Requires the **admin** role.

    - **name**: Administrator-defined department name (e.g. "Computer Science") — must not already exist.
    - **code**: Administrator-defined short code (e.g. "CSE") — must not already exist.
    - **is_active**: Whether the department is active/selectable (default true).
    - **description**: Optional free-text notes.

    Raises **409 Conflict** if name or code is already registered.
    """
    return crud.create_department(db=db, payload=payload)


# ---------------------------------------------------------------------------
# GET /departments/  — Retrieve all departments (paginated)
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=PaginatedDepartmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all departments (paginated)",
)
def get_all_departments(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records per page (max 100)"),
    search: str | None = Query(
        None, max_length=100, description="Search term matched against name, code, or description"
    ),
    is_active: bool | None = Query(None, description="Filter by is_active flag"),
    sort_by: Literal["id", "name", "code"] | None = Query(
        None, description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
) -> PaginatedDepartmentResponse:
    """
    Return a paginated list of configured departments.

    - **page**: Page number to retrieve (default 1).
    - **limit**: Number of records per page (default 10, max 100).
    - **search**: Optional substring match against name, code, or description.
    - **is_active**: Optional exact is_active filter.
    - **sort_by**: Optional field to sort by (id, name, code).
    - **sort_order**: Sort direction, "asc" or "desc" (default "asc").
    """
    departments, total_records = crud.get_paginated_departments(
        db=db,
        page=page,
        limit=limit,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    return PaginatedDepartmentResponse(
        departments=departments,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=limit,
    )


# ---------------------------------------------------------------------------
# GET /departments/{department_id}  — Retrieve a single department
# ---------------------------------------------------------------------------
@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a department by ID",
)
def get_department(
    department_id: int = Path(..., gt=0, description="Primary key of the department"),
    db: Session = Depends(get_db),
) -> DepartmentResponse:
    """
    Fetch a single department by its primary key.

    Raises **404 Not Found** if no department with that ID exists.
    """
    department = crud.get_department_by_id(db=db, department_id=department_id)
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found.",
        )
    return department


# ---------------------------------------------------------------------------
# PUT /departments/{department_id}  — Update a department
# ---------------------------------------------------------------------------
@router.put(
    "/{department_id}",
    response_model=DepartmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a department by ID",
)
def update_department(
    payload: DepartmentUpdate,
    department_id: int = Path(..., gt=0, description="Primary key of the department"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> DepartmentResponse:
    """
    Update a department's details by its primary key. Requires the **admin** role.

    Also used to activate/deactivate a department by toggling **is_active**.

    Raises **404 Not Found** if no department with that ID exists.
    Raises **409 Conflict** if renaming to a name/code already in use.
    """
    department = crud.update_department(db=db, department_id=department_id, payload=payload)
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found.",
        )
    return department


# ---------------------------------------------------------------------------
# DELETE /departments/{department_id}  — Delete a department
# ---------------------------------------------------------------------------
@router.delete(
    "/{department_id}",
    response_model=DepartmentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a department by ID",
)
def delete_department(
    department_id: int = Path(..., gt=0, description="Primary key of the department"),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(Role.ADMIN)),
) -> DepartmentDeleteResponse:
    """
    Permanently remove a department record by its primary key. Requires the **admin** role.

    Raises **404 Not Found** if no department with that ID exists.
    Returns a success message on deletion.
    """
    department = crud.delete_department(db=db, department_id=department_id)
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found.",
        )
    return DepartmentDeleteResponse(
        message=f"Department with ID {department_id} deleted successfully."
    )
