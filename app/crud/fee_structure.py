from fastapi import HTTPException, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.academic_session import AcademicSession
from app.models.fee_structure import FeeStructure
from app.models.program import Program
from app.models.semester import Semester
from app.schemas.fee_structure import FeeStructureCreate, FeeStructureUpdate


def _check_references_exist(
    db: Session, program_id: int, semester_id: int, academic_session_id: int
) -> None:
    if db.query(Program).filter(Program.id == program_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program with ID {program_id} not found.",
        )

    semester = db.query(Semester).filter(Semester.id == semester_id).first()
    if semester is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semester with ID {semester_id} not found.",
        )
    if semester.program_id != program_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Semester with ID {semester_id} does not belong to program {program_id}.",
        )

    if db.query(AcademicSession).filter(AcademicSession.id == academic_session_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic session with ID {academic_session_id} not found.",
        )


def _check_duplicate(
    db: Session,
    program_id: int,
    semester_id: int,
    academic_session_id: int,
    name: str,
    exclude_id: int | None = None,
) -> None:
    """
    Fee name only needs to be unique within the same program+semester+academic
    session — the same fee name (e.g. "Tuition Fee") is expected to repeat
    across different programs/semesters/sessions.
    """
    query = db.query(FeeStructure).filter(
        FeeStructure.program_id == program_id,
        FeeStructure.semester_id == semester_id,
        FeeStructure.academic_session_id == academic_session_id,
        FeeStructure.name == name,
    )
    if exclude_id is not None:
        query = query.filter(FeeStructure.id != exclude_id)

    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A fee structure named '{name}' already exists for this program, "
                f"semester, and academic session."
            ),
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_fee_structure(db: Session, payload: FeeStructureCreate) -> FeeStructure:
    """
    Insert a new fee structure record into the database.

    Raises:
        HTTPException 404: If program_id, semester_id, or academic_session_id
                            does not reference an existing record.
        HTTPException 400: If semester_id does not belong to program_id.
        HTTPException 409: If the name is already used within the same
                            program+semester+academic session.

    Returns:
        The newly created FeeStructure ORM instance.
    """
    _check_references_exist(
        db,
        program_id=payload.program_id,
        semester_id=payload.semester_id,
        academic_session_id=payload.academic_session_id,
    )
    _check_duplicate(
        db,
        program_id=payload.program_id,
        semester_id=payload.semester_id,
        academic_session_id=payload.academic_session_id,
        name=payload.name,
    )

    fee_structure = FeeStructure(
        name=payload.name,
        program_id=payload.program_id,
        semester_id=payload.semester_id,
        academic_session_id=payload.academic_session_id,
        amount=payload.amount,
        due_date=payload.due_date,
        is_active=payload.is_active,
        description=payload.description,
    )
    db.add(fee_structure)
    db.commit()
    db.refresh(fee_structure)
    return fee_structure


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_fee_structures(db: Session) -> list[FeeStructure]:
    return db.query(FeeStructure).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_fee_structures(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    program_id: int | None = None,
    semester_id: int | None = None,
    academic_session_id: int | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[FeeStructure], int]:
    """
    Retrieve a page of fee structures along with the total record count.

    Args:
        db:                  Active SQLAlchemy session (injected via Depends).
        page:                1-indexed page number.
        limit:               Maximum number of records to return for the page.
        search:              Optional case-insensitive substring to match against
                             name or description.
        program_id:          Optional exact program_id to filter by.
        semester_id:         Optional exact semester_id to filter by.
        academic_session_id: Optional exact academic_session_id to filter by.
        is_active:           Optional exact is_active flag to filter by.
        sort_by:             Optional field to sort by (id, name, amount, due_date).
        sort_order:          "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (fee structures on the requested page, total number of records).
    """
    query = db.query(FeeStructure)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                FeeStructure.name.ilike(pattern),
                cast(FeeStructure.description, String).ilike(pattern),
            )
        )

    if program_id is not None:
        query = query.filter(FeeStructure.program_id == program_id)

    if semester_id is not None:
        query = query.filter(FeeStructure.semester_id == semester_id)

    if academic_session_id is not None:
        query = query.filter(FeeStructure.academic_session_id == academic_session_id)

    if is_active is not None:
        query = query.filter(FeeStructure.is_active == is_active)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(FeeStructure, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    fee_structures = query.offset(offset).limit(limit).all()
    return fee_structures, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_fee_structure_by_id(db: Session, fee_structure_id: int) -> FeeStructure | None:
    return db.query(FeeStructure).filter(FeeStructure.id == fee_structure_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_fee_structure(
    db: Session, fee_structure_id: int, payload: FeeStructureUpdate
) -> FeeStructure | None:
    fee_structure = get_fee_structure_by_id(db, fee_structure_id)
    if fee_structure is None:
        return None

    references_changed = (
        payload.program_id != fee_structure.program_id
        or payload.semester_id != fee_structure.semester_id
        or payload.academic_session_id != fee_structure.academic_session_id
    )
    if references_changed:
        _check_references_exist(
            db,
            program_id=payload.program_id,
            semester_id=payload.semester_id,
            academic_session_id=payload.academic_session_id,
        )

    if references_changed or payload.name != fee_structure.name:
        _check_duplicate(
            db,
            program_id=payload.program_id,
            semester_id=payload.semester_id,
            academic_session_id=payload.academic_session_id,
            name=payload.name,
            exclude_id=fee_structure_id,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fee_structure, field, value)

    db.commit()
    db.refresh(fee_structure)
    return fee_structure


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_fee_structure(db: Session, fee_structure_id: int) -> FeeStructure | None:
    fee_structure = get_fee_structure_by_id(db, fee_structure_id)
    if fee_structure is None:
        return None

    db.delete(fee_structure)
    db.commit()
    return fee_structure
