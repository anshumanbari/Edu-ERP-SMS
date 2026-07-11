from fastapi import HTTPException, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.program import Program
from app.schemas.program import ProgramCreate, ProgramUpdate


def _check_duplicate(db: Session, name: str, code: str, exclude_id: int | None = None) -> None:
    query = db.query(Program).filter(or_(Program.name == name, Program.code == code))
    if exclude_id is not None:
        query = query.filter(Program.id != exclude_id)

    existing = query.first()
    if existing is not None:
        field = "name" if existing.name == name else "code"
        value = name if field == "name" else code
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A program with {field} '{value}' already exists.",
        )


def _check_department_exists(db: Session, department_id: int) -> None:
    if db.query(Department).filter(Department.id == department_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found.",
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_program(db: Session, payload: ProgramCreate) -> Program:
    """
    Insert a new program record into the database.

    Raises:
        HTTPException 404: If department_id does not reference an existing department.
        HTTPException 409: If the name or code is already registered.

    Returns:
        The newly created Program ORM instance.
    """
    _check_department_exists(db, payload.department_id)
    _check_duplicate(db, name=payload.name, code=payload.code)

    program = Program(
        name=payload.name,
        code=payload.code,
        department_id=payload.department_id,
        is_active=payload.is_active,
        description=payload.description,
    )
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_programs(db: Session) -> list[Program]:
    return db.query(Program).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_programs(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    department_id: int | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Program], int]:
    """
    Retrieve a page of programs along with the total record count.

    Args:
        db:            Active SQLAlchemy session (injected via Depends).
        page:          1-indexed page number.
        limit:         Maximum number of records to return for the page.
        search:        Optional case-insensitive substring to match against
                       name, code, or description.
        department_id: Optional exact department_id to filter by.
        is_active:     Optional exact is_active flag to filter by.
        sort_by:       Optional field to sort by (id, name, code).
        sort_order:    "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (programs on the requested page, total number of records).
    """
    query = db.query(Program)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Program.name.ilike(pattern),
                Program.code.ilike(pattern),
                cast(Program.description, String).ilike(pattern),
            )
        )

    if department_id is not None:
        query = query.filter(Program.department_id == department_id)

    if is_active is not None:
        query = query.filter(Program.is_active == is_active)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Program, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    programs = query.offset(offset).limit(limit).all()
    return programs, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_program_by_id(db: Session, program_id: int) -> Program | None:
    return db.query(Program).filter(Program.id == program_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_program(db: Session, program_id: int, payload: ProgramUpdate) -> Program | None:
    program = get_program_by_id(db, program_id)
    if program is None:
        return None

    if payload.department_id != program.department_id:
        _check_department_exists(db, payload.department_id)

    if payload.name != program.name or payload.code != program.code:
        _check_duplicate(db, name=payload.name, code=payload.code, exclude_id=program_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(program, field, value)

    db.commit()
    db.refresh(program)
    return program


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_program(db: Session, program_id: int) -> Program | None:
    program = get_program_by_id(db, program_id)
    if program is None:
        return None

    db.delete(program)
    db.commit()
    return program
