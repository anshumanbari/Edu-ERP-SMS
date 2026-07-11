from fastapi import HTTPException, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate


def _check_duplicate(
    db: Session, name: str, code: str, exclude_id: int | None = None
) -> None:
    query = db.query(Department).filter(
        or_(Department.name == name, Department.code == code)
    )
    if exclude_id is not None:
        query = query.filter(Department.id != exclude_id)

    existing = query.first()
    if existing is not None:
        field = "name" if existing.name == name else "code"
        value = name if field == "name" else code
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A department with {field} '{value}' already exists.",
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_department(db: Session, payload: DepartmentCreate) -> Department:
    """
    Insert a new department record into the database.

    Raises:
        HTTPException 409: If the name or code is already registered.

    Returns:
        The newly created Department ORM instance.
    """
    _check_duplicate(db, name=payload.name, code=payload.code)

    department = Department(
        name=payload.name,
        code=payload.code,
        is_active=payload.is_active,
        description=payload.description,
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_departments(db: Session) -> list[Department]:
    return db.query(Department).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_departments(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Department], int]:
    """
    Retrieve a page of departments along with the total record count.

    Args:
        db:         Active SQLAlchemy session (injected via Depends).
        page:       1-indexed page number.
        limit:      Maximum number of records to return for the page.
        search:     Optional case-insensitive substring to match against
                    name, code, or description.
        is_active:  Optional exact is_active flag to filter by.
        sort_by:    Optional field to sort by (id, name, code).
        sort_order: "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (departments on the requested page, total number of records).
    """
    query = db.query(Department)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Department.name.ilike(pattern),
                Department.code.ilike(pattern),
                cast(Department.description, String).ilike(pattern),
            )
        )

    if is_active is not None:
        query = query.filter(Department.is_active == is_active)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Department, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    departments = query.offset(offset).limit(limit).all()
    return departments, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_department_by_id(db: Session, department_id: int) -> Department | None:
    return db.query(Department).filter(Department.id == department_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_department(
    db: Session,
    department_id: int,
    payload: DepartmentUpdate,
) -> Department | None:
    department = get_department_by_id(db, department_id)
    if department is None:
        return None

    if payload.name != department.name or payload.code != department.code:
        _check_duplicate(db, name=payload.name, code=payload.code, exclude_id=department_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(department, field, value)

    db.commit()
    db.refresh(department)
    return department


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_department(db: Session, department_id: int) -> Department | None:
    department = get_department_by_id(db, department_id)
    if department is None:
        return None

    db.delete(department)
    db.commit()
    return department
