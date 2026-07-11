from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_user(db: Session, payload: UserCreate) -> User:
    """
    Insert a new user record into the database.

    Args:
        db:      Active SQLAlchemy session (injected via Depends).
        payload: Validated UserCreate schema.

    Raises:
        HTTPException 409: If the email address is already registered.

    Returns:
        The newly created User ORM instance.
    """
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with email '{payload.email}' is already registered.",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# READ — by email
# ---------------------------------------------------------------------------
def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Fetch a single user by email address.

    Args:
        db:    Active SQLAlchemy session (injected via Depends).
        email: Email address to look up.

    Returns:
        The matching User ORM instance, or None if not found.
    """
    return db.query(User).filter(User.email == email).first()


# ---------------------------------------------------------------------------
# AUTHENTICATE
# ---------------------------------------------------------------------------
def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """
    Verify a user's credentials.

    Args:
        db:       Active SQLAlchemy session (injected via Depends).
        email:    Email address supplied at login.
        password: Plain-text password supplied at login.

    Returns:
        The authenticated User ORM instance, or None if credentials are invalid.
    """
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
