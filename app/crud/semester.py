from fastapi import HTTPException, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.program import Program
from app.models.semester import Semester
from app.schemas.semester import SemesterCreate, SemesterUpdate


def _check_duplicate(
    db: Session,
    program_id: int,
    name: str,
    code: str,
    sequence_number: int,
    exclude_id: int | None = None,
) -> None:
    """
    Semester name/code/sequence_number only need to be unique within the same
    program — the same "Semester 1" label is expected to repeat across programs.
    """
    query = db.query(Semester).filter(
        Semester.program_id == program_id,
        or_(
            Semester.name == name,
            Semester.code == code,
            Semester.sequence_number == sequence_number,
        ),
    )
    if exclude_id is not None:
        query = query.filter(Semester.id != exclude_id)

    existing = query.first()
    if existing is not None:
        if existing.name == name:
            detail = f"A semester named '{name}' already exists for this program."
        elif existing.code == code:
            detail = f"A semester with code '{code}' already exists for this program."
        else:
            detail = f"A semester with sequence_number {sequence_number} already exists for this program."
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def _check_program_exists(db: Session, program_id: int) -> None:
    if db.query(Program).filter(Program.id == program_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program with ID {program_id} not found.",
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_semester(db: Session, payload: SemesterCreate) -> Semester:
    """
    Insert a new semester record into the database.

    Raises:
        HTTPException 404: If program_id does not reference an existing program.
        HTTPException 409: If the name, code, or sequence_number is already
                            used within the same program.

    Returns:
        The newly created Semester ORM instance.
    """
    _check_program_exists(db, payload.program_id)
    _check_duplicate(
        db,
        program_id=payload.program_id,
        name=payload.name,
        code=payload.code,
        sequence_number=payload.sequence_number,
    )

    semester = Semester(
        name=payload.name,
        code=payload.code,
        program_id=payload.program_id,
        sequence_number=payload.sequence_number,
        is_active=payload.is_active,
        description=payload.description,
    )
    db.add(semester)
    db.commit()
    db.refresh(semester)
    return semester


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_semesters(db: Session) -> list[Semester]:
    return db.query(Semester).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_semesters(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    program_id: int | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Semester], int]:
    """
    Retrieve a page of semesters along with the total record count.

    Args:
        db:         Active SQLAlchemy session (injected via Depends).
        page:       1-indexed page number.
        limit:      Maximum number of records to return for the page.
        search:     Optional case-insensitive substring to match against
                    name, code, or description.
        program_id: Optional exact program_id to filter by.
        is_active:  Optional exact is_active flag to filter by.
        sort_by:    Optional field to sort by (id, name, sequence_number).
        sort_order: "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (semesters on the requested page, total number of records).
    """
    query = db.query(Semester)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Semester.name.ilike(pattern),
                Semester.code.ilike(pattern),
                cast(Semester.description, String).ilike(pattern),
            )
        )

    if program_id is not None:
        query = query.filter(Semester.program_id == program_id)

    if is_active is not None:
        query = query.filter(Semester.is_active == is_active)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Semester, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    semesters = query.offset(offset).limit(limit).all()
    return semesters, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_semester_by_id(db: Session, semester_id: int) -> Semester | None:
    return db.query(Semester).filter(Semester.id == semester_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_semester(db: Session, semester_id: int, payload: SemesterUpdate) -> Semester | None:
    semester = get_semester_by_id(db, semester_id)
    if semester is None:
        return None

    if payload.program_id != semester.program_id:
        _check_program_exists(db, payload.program_id)

    if (
        payload.program_id != semester.program_id
        or payload.name != semester.name
        or payload.code != semester.code
        or payload.sequence_number != semester.sequence_number
    ):
        _check_duplicate(
            db,
            program_id=payload.program_id,
            name=payload.name,
            code=payload.code,
            sequence_number=payload.sequence_number,
            exclude_id=semester_id,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(semester, field, value)

    db.commit()
    db.refresh(semester)
    return semester


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_semester(db: Session, semester_id: int) -> Semester | None:
    semester = get_semester_by_id(db, semester_id)
    if semester is None:
        return None

    db.delete(semester)
    db.commit()
    return semester
