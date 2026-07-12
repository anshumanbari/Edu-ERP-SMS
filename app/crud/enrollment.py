from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.academic_session import AcademicSession
from app.models.enrollment import Enrollment
from app.models.program import Program
from app.models.section import Section
from app.models.semester import Semester
from app.models.student import Student
from app.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate


def _check_references_exist(
    db: Session,
    student_id: int,
    academic_session_id: int,
    program_id: int,
    semester_id: int,
    section_id: int,
) -> None:
    if db.query(Student).filter(Student.id == student_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )
    if db.query(AcademicSession).filter(AcademicSession.id == academic_session_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic session with ID {academic_session_id} not found.",
        )
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

    section = db.query(Section).filter(Section.id == section_id).first()
    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section with ID {section_id} not found.",
        )
    if section.program_id != program_id or section.semester_id != semester_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Section with ID {section_id} does not belong to program {program_id} and semester {semester_id}.",
        )


def _check_duplicate(
    db: Session,
    student_id: int,
    academic_session_id: int,
    exclude_id: int | None = None,
) -> None:
    """
    A student can only hold one enrollment per academic session.
    """
    query = db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.academic_session_id == academic_session_id,
    )
    if exclude_id is not None:
        query = query.filter(Enrollment.id != exclude_id)

    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Student {student_id} is already enrolled for academic session {academic_session_id}."
            ),
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_enrollment(db: Session, payload: EnrollmentCreate) -> Enrollment:
    """
    Insert a new enrollment record into the database.

    Raises:
        HTTPException 404: If student_id, academic_session_id, program_id, semester_id,
                            or section_id does not reference an existing record.
        HTTPException 400: If semester_id does not belong to program_id, or section_id
                            does not belong to program_id/semester_id.
        HTTPException 409: If the student is already enrolled for the academic session.

    Returns:
        The newly created Enrollment ORM instance.
    """
    _check_references_exist(
        db,
        student_id=payload.student_id,
        academic_session_id=payload.academic_session_id,
        program_id=payload.program_id,
        semester_id=payload.semester_id,
        section_id=payload.section_id,
    )
    _check_duplicate(
        db,
        student_id=payload.student_id,
        academic_session_id=payload.academic_session_id,
    )

    enrollment = Enrollment(
        student_id=payload.student_id,
        academic_session_id=payload.academic_session_id,
        program_id=payload.program_id,
        semester_id=payload.semester_id,
        section_id=payload.section_id,
        enrollment_date=payload.enrollment_date,
        status=payload.status,
        remarks=payload.remarks,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_enrollments(db: Session) -> list[Enrollment]:
    return db.query(Enrollment).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_enrollments(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    student_id: int | None = None,
    academic_session_id: int | None = None,
    program_id: int | None = None,
    semester_id: int | None = None,
    section_id: int | None = None,
    status_filter: str | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[Enrollment], int]:
    """
    Retrieve a page of enrollments along with the total record count.

    Args:
        db:                  Active SQLAlchemy session (injected via Depends).
        page:                1-indexed page number.
        limit:               Maximum number of records to return for the page.
        search:              Optional case-insensitive substring to match against remarks.
        student_id:          Optional exact student_id to filter by.
        academic_session_id: Optional exact academic_session_id to filter by.
        program_id:          Optional exact program_id to filter by.
        semester_id:         Optional exact semester_id to filter by.
        section_id:          Optional exact section_id to filter by.
        status_filter:       Optional exact status to filter by.
        sort_by:             Optional field to sort by (id, enrollment_date, status).
        sort_order:          "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (enrollments on the requested page, total number of records).
    """
    query = db.query(Enrollment)

    if search:
        pattern = f"%{search}%"
        query = query.filter(Enrollment.remarks.ilike(pattern))

    if student_id is not None:
        query = query.filter(Enrollment.student_id == student_id)

    if academic_session_id is not None:
        query = query.filter(Enrollment.academic_session_id == academic_session_id)

    if program_id is not None:
        query = query.filter(Enrollment.program_id == program_id)

    if semester_id is not None:
        query = query.filter(Enrollment.semester_id == semester_id)

    if section_id is not None:
        query = query.filter(Enrollment.section_id == section_id)

    if status_filter:
        query = query.filter(Enrollment.status == status_filter)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(Enrollment, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    enrollments = query.offset(offset).limit(limit).all()
    return enrollments, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_enrollment_by_id(db: Session, enrollment_id: int) -> Enrollment | None:
    return db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_enrollment(db: Session, enrollment_id: int, payload: EnrollmentUpdate) -> Enrollment | None:
    enrollment = get_enrollment_by_id(db, enrollment_id)
    if enrollment is None:
        return None

    references_changed = (
        payload.student_id != enrollment.student_id
        or payload.academic_session_id != enrollment.academic_session_id
        or payload.program_id != enrollment.program_id
        or payload.semester_id != enrollment.semester_id
        or payload.section_id != enrollment.section_id
    )
    if references_changed:
        _check_references_exist(
            db,
            student_id=payload.student_id,
            academic_session_id=payload.academic_session_id,
            program_id=payload.program_id,
            semester_id=payload.semester_id,
            section_id=payload.section_id,
        )

    if (
        payload.student_id != enrollment.student_id
        or payload.academic_session_id != enrollment.academic_session_id
    ):
        _check_duplicate(
            db,
            student_id=payload.student_id,
            academic_session_id=payload.academic_session_id,
            exclude_id=enrollment_id,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(enrollment, field, value)

    db.commit()
    db.refresh(enrollment)
    return enrollment


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_enrollment(db: Session, enrollment_id: int) -> Enrollment | None:
    enrollment = get_enrollment_by_id(db, enrollment_id)
    if enrollment is None:
        return None

    db.delete(enrollment)
    db.commit()
    return enrollment
