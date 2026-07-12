from datetime import time

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.academic_session import AcademicSession
from app.models.classroom import Classroom
from app.models.section import Section
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.timetable import Timetable
from app.schemas.timetable import TimetableCreate, TimetableUpdate


def _check_references_exist(
    db: Session,
    section_id: int,
    subject_id: int,
    teacher_id: int,
    classroom_id: int,
    academic_session_id: int,
) -> None:
    if db.query(Section).filter(Section.id == section_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section with ID {section_id} not found.",
        )
    if db.query(Subject).filter(Subject.id == subject_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )
    if db.query(Teacher).filter(Teacher.id == teacher_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with ID {teacher_id} not found.",
        )
    if db.query(Classroom).filter(Classroom.id == classroom_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Classroom with ID {classroom_id} not found.",
        )
    if db.query(AcademicSession).filter(AcademicSession.id == academic_session_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic session with ID {academic_session_id} not found.",
        )


def _overlaps(existing_start: time, existing_end: time, new_start: time, new_end: time) -> bool:
    return existing_start < new_end and existing_end > new_start


def _check_conflicts(
    db: Session,
    section_id: int,
    teacher_id: int,
    classroom_id: int,
    academic_session_id: int,
    day_of_week: str,
    start_time: time,
    end_time: time,
    exclude_id: int | None = None,
) -> None:
    """
    A section, teacher, or classroom cannot be double-booked for an
    overlapping time range on the same day within the same academic session.
    """
    query = db.query(Timetable).filter(
        Timetable.academic_session_id == academic_session_id,
        Timetable.day_of_week == day_of_week,
    )
    if exclude_id is not None:
        query = query.filter(Timetable.id != exclude_id)

    for entry in query.all():
        if not _overlaps(entry.start_time, entry.end_time, start_time, end_time):
            continue

        if entry.section_id == section_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Section {section_id} already has a class scheduled on {day_of_week} "
                    f"from {entry.start_time} to {entry.end_time}."
                ),
            )
        if entry.teacher_id == teacher_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Teacher {teacher_id} already has a class scheduled on {day_of_week} "
                    f"from {entry.start_time} to {entry.end_time}."
                ),
            )
        if entry.classroom_id == classroom_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Classroom {classroom_id} is already booked on {day_of_week} "
                    f"from {entry.start_time} to {entry.end_time}."
                ),
            )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_timetable_entry(db: Session, payload: TimetableCreate) -> Timetable:
    """
    Insert a new timetable entry into the database.

    Raises:
        HTTPException 404: If section_id, subject_id, teacher_id, classroom_id, or
                            academic_session_id does not reference an existing record.
        HTTPException 409: If the section, teacher, or classroom already has an
                            overlapping class scheduled on the same day.

    Returns:
        The newly created Timetable ORM instance.
    """
    _check_references_exist(
        db,
        section_id=payload.section_id,
        subject_id=payload.subject_id,
        teacher_id=payload.teacher_id,
        classroom_id=payload.classroom_id,
        academic_session_id=payload.academic_session_id,
    )
    _check_conflicts(
        db,
        section_id=payload.section_id,
        teacher_id=payload.teacher_id,
        classroom_id=payload.classroom_id,
        academic_session_id=payload.academic_session_id,
        day_of_week=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )

    entry = Timetable(
        section_id=payload.section_id,
        subject_id=payload.subject_id,
        teacher_id=payload.teacher_id,
        classroom_id=payload.classroom_id,
        academic_session_id=payload.academic_session_id,
        day_of_week=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
        is_active=payload.is_active,
        remarks=payload.remarks,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_timetable_entries(db: Session) -> list[Timetable]:
    return db.query(Timetable).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_timetable_entries(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    section_id: int | None = None,
    subject_id: int | None = None,
    teacher_id: int | None = None,
    classroom_id: int | None = None,
    academic_session_id: int | None = None,
    day_of_week: str | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Timetable], int]:
    """
    Retrieve a page of timetable entries along with the total record count.

    Args:
        db:                  Active SQLAlchemy session (injected via Depends).
        page:                1-indexed page number.
        limit:               Maximum number of records to return for the page.
        search:              Optional case-insensitive substring to match against remarks.
        section_id:          Optional exact section_id to filter by.
        subject_id:          Optional exact subject_id to filter by.
        teacher_id:          Optional exact teacher_id to filter by.
        classroom_id:        Optional exact classroom_id to filter by.
        academic_session_id: Optional exact academic_session_id to filter by.
        day_of_week:         Optional exact day_of_week to filter by.
        is_active:           Optional exact is_active flag to filter by.
        sort_by:             Optional field to sort by (id, day_of_week, start_time).
        sort_order:          "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (timetable entries on the requested page, total number of records).
    """
    query = db.query(Timetable)

    if search:
        pattern = f"%{search}%"
        query = query.filter(Timetable.remarks.ilike(pattern))

    if section_id is not None:
        query = query.filter(Timetable.section_id == section_id)

    if subject_id is not None:
        query = query.filter(Timetable.subject_id == subject_id)

    if teacher_id is not None:
        query = query.filter(Timetable.teacher_id == teacher_id)

    if classroom_id is not None:
        query = query.filter(Timetable.classroom_id == classroom_id)

    if academic_session_id is not None:
        query = query.filter(Timetable.academic_session_id == academic_session_id)

    if day_of_week:
        query = query.filter(Timetable.day_of_week == day_of_week)

    if is_active is not None:
        query = query.filter(Timetable.is_active == is_active)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Timetable, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    entries = query.offset(offset).limit(limit).all()
    return entries, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_timetable_entry_by_id(db: Session, timetable_id: int) -> Timetable | None:
    return db.query(Timetable).filter(Timetable.id == timetable_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_timetable_entry(
    db: Session, timetable_id: int, payload: TimetableUpdate
) -> Timetable | None:
    entry = get_timetable_entry_by_id(db, timetable_id)
    if entry is None:
        return None

    references_changed = (
        payload.section_id != entry.section_id
        or payload.subject_id != entry.subject_id
        or payload.teacher_id != entry.teacher_id
        or payload.classroom_id != entry.classroom_id
        or payload.academic_session_id != entry.academic_session_id
    )
    if references_changed:
        _check_references_exist(
            db,
            section_id=payload.section_id,
            subject_id=payload.subject_id,
            teacher_id=payload.teacher_id,
            classroom_id=payload.classroom_id,
            academic_session_id=payload.academic_session_id,
        )

    schedule_changed = (
        references_changed
        or payload.day_of_week != entry.day_of_week
        or payload.start_time != entry.start_time
        or payload.end_time != entry.end_time
    )
    if schedule_changed:
        _check_conflicts(
            db,
            section_id=payload.section_id,
            teacher_id=payload.teacher_id,
            classroom_id=payload.classroom_id,
            academic_session_id=payload.academic_session_id,
            day_of_week=payload.day_of_week,
            start_time=payload.start_time,
            end_time=payload.end_time,
            exclude_id=timetable_id,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)

    db.commit()
    db.refresh(entry)
    return entry


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_timetable_entry(db: Session, timetable_id: int) -> Timetable | None:
    entry = get_timetable_entry_by_id(db, timetable_id)
    if entry is None:
        return None

    db.delete(entry)
    db.commit()
    return entry
