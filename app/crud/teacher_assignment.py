from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.academic_session import AcademicSession
from app.models.section import Section
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.teacher_assignment import TeacherAssignment
from app.schemas.teacher_assignment import TeacherAssignmentCreate, TeacherAssignmentUpdate


def _check_references_exist(
    db: Session,
    teacher_id: int,
    subject_id: int,
    section_id: int,
    academic_session_id: int,
) -> None:
    if db.query(Teacher).filter(Teacher.id == teacher_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with ID {teacher_id} not found.",
        )
    if db.query(Subject).filter(Subject.id == subject_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )
    if db.query(Section).filter(Section.id == section_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section with ID {section_id} not found.",
        )
    if db.query(AcademicSession).filter(AcademicSession.id == academic_session_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic session with ID {academic_session_id} not found.",
        )


def _check_duplicate(
    db: Session,
    subject_id: int,
    section_id: int,
    academic_session_id: int,
    exclude_id: int | None = None,
) -> None:
    """
    A subject+section combination can only have one teacher assignment per
    academic session.
    """
    query = db.query(TeacherAssignment).filter(
        TeacherAssignment.subject_id == subject_id,
        TeacherAssignment.section_id == section_id,
        TeacherAssignment.academic_session_id == academic_session_id,
    )
    if exclude_id is not None:
        query = query.filter(TeacherAssignment.id != exclude_id)

    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Subject {subject_id} in section {section_id} already has a teacher "
                f"assigned for academic session {academic_session_id}."
            ),
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_teacher_assignment(
    db: Session, payload: TeacherAssignmentCreate
) -> TeacherAssignment:
    """
    Insert a new teacher assignment record into the database.

    Raises:
        HTTPException 404: If teacher_id, subject_id, section_id, or academic_session_id
                            does not reference an existing record.
        HTTPException 409: If the subject+section already has a teacher assigned for
                            the academic session.

    Returns:
        The newly created TeacherAssignment ORM instance.
    """
    _check_references_exist(
        db,
        teacher_id=payload.teacher_id,
        subject_id=payload.subject_id,
        section_id=payload.section_id,
        academic_session_id=payload.academic_session_id,
    )
    _check_duplicate(
        db,
        subject_id=payload.subject_id,
        section_id=payload.section_id,
        academic_session_id=payload.academic_session_id,
    )

    assignment = TeacherAssignment(
        teacher_id=payload.teacher_id,
        subject_id=payload.subject_id,
        section_id=payload.section_id,
        academic_session_id=payload.academic_session_id,
        is_active=payload.is_active,
        remarks=payload.remarks,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_teacher_assignments(db: Session) -> list[TeacherAssignment]:
    return db.query(TeacherAssignment).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_teacher_assignments(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    teacher_id: int | None = None,
    subject_id: int | None = None,
    section_id: int | None = None,
    academic_session_id: int | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[TeacherAssignment], int]:
    """
    Retrieve a page of teacher assignments along with the total record count.

    Args:
        db:                  Active SQLAlchemy session (injected via Depends).
        page:                1-indexed page number.
        limit:               Maximum number of records to return for the page.
        search:              Optional case-insensitive substring to match against remarks.
        teacher_id:          Optional exact teacher_id to filter by.
        subject_id:          Optional exact subject_id to filter by.
        section_id:          Optional exact section_id to filter by.
        academic_session_id: Optional exact academic_session_id to filter by.
        is_active:           Optional exact is_active flag to filter by.
        sort_by:             Optional field to sort by (id).
        sort_order:          "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (teacher assignments on the requested page, total number of records).
    """
    query = db.query(TeacherAssignment)

    if search:
        pattern = f"%{search}%"
        query = query.filter(TeacherAssignment.remarks.ilike(pattern))

    if teacher_id is not None:
        query = query.filter(TeacherAssignment.teacher_id == teacher_id)

    if subject_id is not None:
        query = query.filter(TeacherAssignment.subject_id == subject_id)

    if section_id is not None:
        query = query.filter(TeacherAssignment.section_id == section_id)

    if academic_session_id is not None:
        query = query.filter(TeacherAssignment.academic_session_id == academic_session_id)

    if is_active is not None:
        query = query.filter(TeacherAssignment.is_active == is_active)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(TeacherAssignment, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    assignments = query.offset(offset).limit(limit).all()
    return assignments, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_teacher_assignment_by_id(
    db: Session, assignment_id: int
) -> TeacherAssignment | None:
    return db.query(TeacherAssignment).filter(TeacherAssignment.id == assignment_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_teacher_assignment(
    db: Session, assignment_id: int, payload: TeacherAssignmentUpdate
) -> TeacherAssignment | None:
    assignment = get_teacher_assignment_by_id(db, assignment_id)
    if assignment is None:
        return None

    references_changed = (
        payload.teacher_id != assignment.teacher_id
        or payload.subject_id != assignment.subject_id
        or payload.section_id != assignment.section_id
        or payload.academic_session_id != assignment.academic_session_id
    )
    if references_changed:
        _check_references_exist(
            db,
            teacher_id=payload.teacher_id,
            subject_id=payload.subject_id,
            section_id=payload.section_id,
            academic_session_id=payload.academic_session_id,
        )

    if (
        payload.subject_id != assignment.subject_id
        or payload.section_id != assignment.section_id
        or payload.academic_session_id != assignment.academic_session_id
    ):
        _check_duplicate(
            db,
            subject_id=payload.subject_id,
            section_id=payload.section_id,
            academic_session_id=payload.academic_session_id,
            exclude_id=assignment_id,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)

    db.commit()
    db.refresh(assignment)
    return assignment


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_teacher_assignment(
    db: Session, assignment_id: int
) -> TeacherAssignment | None:
    assignment = get_teacher_assignment_by_id(db, assignment_id)
    if assignment is None:
        return None

    db.delete(assignment)
    db.commit()
    return assignment
