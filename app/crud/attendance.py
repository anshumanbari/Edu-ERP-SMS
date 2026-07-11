from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.academic_session import AcademicSession
from app.models.attendance import Attendance
from app.models.student import Student
from app.models.subject import Subject
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate


def _check_references_exist(
    db: Session, student_id: int, subject_id: int, academic_session_id: int
) -> None:
    if db.query(Student).filter(Student.id == student_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )
    if db.query(Subject).filter(Subject.id == subject_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )
    if db.query(AcademicSession).filter(AcademicSession.id == academic_session_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic session with ID {academic_session_id} not found.",
        )


def _check_duplicate(
    db: Session,
    student_id: int,
    subject_id: int,
    attendance_date,
    exclude_id: int | None = None,
) -> None:
    """
    A student can only have one attendance record per subject per day.
    """
    query = db.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.subject_id == subject_id,
        Attendance.attendance_date == attendance_date,
    )
    if exclude_id is not None:
        query = query.filter(Attendance.id != exclude_id)

    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Attendance for student {student_id} in subject {subject_id} "
                f"on {attendance_date} is already recorded."
            ),
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_attendance(db: Session, payload: AttendanceCreate, marked_by_id: int) -> Attendance:
    """
    Insert a new attendance record into the database.

    Args:
        db:            Active SQLAlchemy session (injected via Depends).
        payload:       Validated AttendanceCreate schema.
        marked_by_id:  Primary key of the authenticated user recording the entry
                       (taken from the JWT-authenticated session, never client-supplied).

    Raises:
        HTTPException 404: If student_id, subject_id, or academic_session_id does
                            not reference an existing record.
        HTTPException 409: If attendance for this student/subject/date is already recorded.

    Returns:
        The newly created Attendance ORM instance.
    """
    _check_references_exist(
        db,
        student_id=payload.student_id,
        subject_id=payload.subject_id,
        academic_session_id=payload.academic_session_id,
    )
    _check_duplicate(
        db,
        student_id=payload.student_id,
        subject_id=payload.subject_id,
        attendance_date=payload.attendance_date,
    )

    attendance = Attendance(
        student_id=payload.student_id,
        subject_id=payload.subject_id,
        academic_session_id=payload.academic_session_id,
        attendance_date=payload.attendance_date,
        status=payload.status,
        marked_by_id=marked_by_id,
        remarks=payload.remarks,
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_attendance_records(db: Session) -> list[Attendance]:
    return db.query(Attendance).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_attendance_records(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    student_id: int | None = None,
    subject_id: int | None = None,
    academic_session_id: int | None = None,
    status_filter: str | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Attendance], int]:
    """
    Retrieve a page of attendance records along with the total record count.

    Args:
        db:                  Active SQLAlchemy session (injected via Depends).
        page:                1-indexed page number.
        limit:               Maximum number of records to return for the page.
        search:              Optional case-insensitive substring to match against remarks.
        student_id:          Optional exact student_id to filter by.
        subject_id:          Optional exact subject_id to filter by.
        academic_session_id: Optional exact academic_session_id to filter by.
        status_filter:       Optional exact status to filter by.
        sort_by:             Optional field to sort by (id, attendance_date, status).
        sort_order:          "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (attendance records on the requested page, total number of records).
    """
    query = db.query(Attendance)

    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Attendance.remarks.ilike(pattern)))

    if student_id is not None:
        query = query.filter(Attendance.student_id == student_id)

    if subject_id is not None:
        query = query.filter(Attendance.subject_id == subject_id)

    if academic_session_id is not None:
        query = query.filter(Attendance.academic_session_id == academic_session_id)

    if status_filter:
        query = query.filter(Attendance.status == status_filter)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Attendance, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    attendance_records = query.offset(offset).limit(limit).all()
    return attendance_records, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_attendance_by_id(db: Session, attendance_id: int) -> Attendance | None:
    return db.query(Attendance).filter(Attendance.id == attendance_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_attendance(
    db: Session, attendance_id: int, payload: AttendanceUpdate
) -> Attendance | None:
    attendance = get_attendance_by_id(db, attendance_id)
    if attendance is None:
        return None

    references_changed = (
        payload.student_id != attendance.student_id
        or payload.subject_id != attendance.subject_id
        or payload.academic_session_id != attendance.academic_session_id
    )
    if references_changed:
        _check_references_exist(
            db,
            student_id=payload.student_id,
            subject_id=payload.subject_id,
            academic_session_id=payload.academic_session_id,
        )

    if (
        references_changed
        or payload.attendance_date != attendance.attendance_date
    ):
        _check_duplicate(
            db,
            student_id=payload.student_id,
            subject_id=payload.subject_id,
            attendance_date=payload.attendance_date,
            exclude_id=attendance_id,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(attendance, field, value)

    db.commit()
    db.refresh(attendance)
    return attendance


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_attendance(db: Session, attendance_id: int) -> Attendance | None:
    attendance = get_attendance_by_id(db, attendance_id)
    if attendance is None:
        return None

    db.delete(attendance)
    db.commit()
    return attendance
