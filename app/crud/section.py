from fastapi import HTTPException, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.program import Program
from app.models.section import Section
from app.models.semester import Semester
from app.schemas.section import SectionCreate, SectionUpdate


def _check_references_exist(db: Session, program_id: int, semester_id: int) -> None:
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


def _check_duplicate(
    db: Session,
    program_id: int,
    semester_id: int,
    name: str,
    code: str,
    exclude_id: int | None = None,
) -> None:
    """
    Section name/code only need to be unique within the same program+semester —
    "Section A" is expected to repeat across different programs/semesters.
    """
    query = db.query(Section).filter(
        Section.program_id == program_id,
        Section.semester_id == semester_id,
        or_(Section.name == name, Section.code == code),
    )
    if exclude_id is not None:
        query = query.filter(Section.id != exclude_id)

    existing = query.first()
    if existing is not None:
        field = "name" if existing.name == name else "code"
        value = name if field == "name" else code
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A section with {field} '{value}' already exists for this program and semester.",
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_section(db: Session, payload: SectionCreate) -> Section:
    """
    Insert a new section record into the database.

    Raises:
        HTTPException 404: If program_id or semester_id does not reference an existing record.
        HTTPException 400: If semester_id does not belong to program_id.
        HTTPException 409: If the name or code is already used within the same program+semester.

    Returns:
        The newly created Section ORM instance.
    """
    _check_references_exist(db, program_id=payload.program_id, semester_id=payload.semester_id)
    _check_duplicate(
        db,
        program_id=payload.program_id,
        semester_id=payload.semester_id,
        name=payload.name,
        code=payload.code,
    )

    section = Section(
        name=payload.name,
        code=payload.code,
        program_id=payload.program_id,
        semester_id=payload.semester_id,
        is_active=payload.is_active,
        description=payload.description,
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_sections(db: Session) -> list[Section]:
    return db.query(Section).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_sections(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    program_id: int | None = None,
    semester_id: int | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Section], int]:
    """
    Retrieve a page of sections along with the total record count.

    Args:
        db:          Active SQLAlchemy session (injected via Depends).
        page:        1-indexed page number.
        limit:       Maximum number of records to return for the page.
        search:      Optional case-insensitive substring to match against
                     name, code, or description.
        program_id:  Optional exact program_id to filter by.
        semester_id: Optional exact semester_id to filter by.
        is_active:   Optional exact is_active flag to filter by.
        sort_by:     Optional field to sort by (id, name, code).
        sort_order:  "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (sections on the requested page, total number of records).
    """
    query = db.query(Section)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Section.name.ilike(pattern),
                Section.code.ilike(pattern),
                cast(Section.description, String).ilike(pattern),
            )
        )

    if program_id is not None:
        query = query.filter(Section.program_id == program_id)

    if semester_id is not None:
        query = query.filter(Section.semester_id == semester_id)

    if is_active is not None:
        query = query.filter(Section.is_active == is_active)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Section, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    sections = query.offset(offset).limit(limit).all()
    return sections, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_section_by_id(db: Session, section_id: int) -> Section | None:
    return db.query(Section).filter(Section.id == section_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_section(db: Session, section_id: int, payload: SectionUpdate) -> Section | None:
    section = get_section_by_id(db, section_id)
    if section is None:
        return None

    references_changed = (
        payload.program_id != section.program_id or payload.semester_id != section.semester_id
    )
    if references_changed:
        _check_references_exist(db, program_id=payload.program_id, semester_id=payload.semester_id)

    if references_changed or payload.name != section.name or payload.code != section.code:
        _check_duplicate(
            db,
            program_id=payload.program_id,
            semester_id=payload.semester_id,
            name=payload.name,
            code=payload.code,
            exclude_id=section_id,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(section, field, value)

    db.commit()
    db.refresh(section)
    return section


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_section(db: Session, section_id: int) -> Section | None:
    section = get_section_by_id(db, section_id)
    if section is None:
        return None

    db.delete(section)
    db.commit()
    return section
