from fastapi import HTTPException, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.academic_session import AcademicSession
from app.schemas.academic_session import AcademicSessionCreate, AcademicSessionUpdate


def _clear_other_current_sessions(db: Session, exclude_id: int | None = None) -> None:
    """
    Unset is_current on every other session so at most one session is ever
    flagged as current at a time.
    """
    query = db.query(AcademicSession).filter(AcademicSession.is_current.is_(True))
    if exclude_id is not None:
        query = query.filter(AcademicSession.id != exclude_id)
    query.update({AcademicSession.is_current: False})


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_academic_session(db: Session, payload: AcademicSessionCreate) -> AcademicSession:
    """
    Insert a new academic session record into the database.

    Raises:
        HTTPException 409: If the session_name is already registered.

    Returns:
        The newly created AcademicSession ORM instance.
    """
    if db.query(AcademicSession).filter(AcademicSession.session_name == payload.session_name).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An academic session named '{payload.session_name}' already exists.",
        )

    if payload.is_current:
        _clear_other_current_sessions(db)

    academic_session = AcademicSession(
        session_name=payload.session_name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=payload.status,
        is_current=payload.is_current,
        description=payload.description,
    )
    db.add(academic_session)
    db.commit()
    db.refresh(academic_session)
    return academic_session


# ---------------------------------------------------------------------------
# READ — all
# ---------------------------------------------------------------------------
def get_all_academic_sessions(db: Session) -> list[AcademicSession]:
    return db.query(AcademicSession).all()


# ---------------------------------------------------------------------------
# READ — paginated
# ---------------------------------------------------------------------------
def get_paginated_academic_sessions(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    status_filter: str | None = None,
    is_current: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> tuple[list[AcademicSession], int]:
    """
    Retrieve a page of academic sessions along with the total record count.

    Args:
        db:            Active SQLAlchemy session (injected via Depends).
        page:          1-indexed page number.
        limit:         Maximum number of records to return for the page.
        search:        Optional case-insensitive substring to match against
                       session_name or description.
        status_filter: Optional exact status to filter by.
        is_current:    Optional exact is_current flag to filter by.
        sort_by:       Optional field to sort by (id, session_name, start_date).
        sort_order:    "asc" or "desc" (defaults to "asc").

    Returns:
        A tuple of (academic sessions on the requested page, total number of records).
    """
    query = db.query(AcademicSession)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                AcademicSession.session_name.ilike(pattern),
                cast(AcademicSession.description, String).ilike(pattern),
            )
        )

    if status_filter:
        query = query.filter(AcademicSession.status == status_filter)

    if is_current is not None:
        query = query.filter(AcademicSession.is_current == is_current)

    total_records = query.count()

    if sort_by:
        sort_column = getattr(AcademicSession, sort_by)
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * limit
    academic_sessions = query.offset(offset).limit(limit).all()
    return academic_sessions, total_records


# ---------------------------------------------------------------------------
# READ — single
# ---------------------------------------------------------------------------
def get_academic_session_by_id(db: Session, academic_session_id: int) -> AcademicSession | None:
    return db.query(AcademicSession).filter(AcademicSession.id == academic_session_id).first()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_academic_session(
    db: Session,
    academic_session_id: int,
    payload: AcademicSessionUpdate,
) -> AcademicSession | None:
    academic_session = get_academic_session_by_id(db, academic_session_id)
    if academic_session is None:
        return None

    if payload.session_name != academic_session.session_name:
        duplicate = (
            db.query(AcademicSession)
            .filter(
                AcademicSession.session_name == payload.session_name,
                AcademicSession.id != academic_session_id,
            )
            .first()
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An academic session named '{payload.session_name}' already exists.",
            )

    if payload.is_current:
        _clear_other_current_sessions(db, exclude_id=academic_session_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(academic_session, field, value)

    db.commit()
    db.refresh(academic_session)
    return academic_session


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_academic_session(db: Session, academic_session_id: int) -> AcademicSession | None:
    academic_session = get_academic_session_by_id(db, academic_session_id)
    if academic_session is None:
        return None

    db.delete(academic_session)
    db.commit()
    return academic_session
