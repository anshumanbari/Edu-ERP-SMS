from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user
from app.crud import user as crud
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ---------------------------------------------------------------------------
# POST /auth/register  — Register a new user
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Register a new user account.

    - **name**: Full name of the user.
    - **email**: Unique email address — must not already exist.
    - **password**: Plain-text password (min 8 characters) — stored hashed.

    Raises **409 Conflict** if the email is already registered.
    """
    return crud.create_user(db=db, payload=payload)


# ---------------------------------------------------------------------------
# POST /auth/login  — Log in and obtain an access token
# ---------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Log in and obtain a JWT access token",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """
    Authenticate with email (as `username`) and password to receive a JWT
    access token. Pass the token as `Authorization: Bearer <token>` on
    subsequent requests.

    Raises **401 Unauthorized** if the credentials are invalid.
    """
    user = crud.authenticate_user(db=db, email=form_data.username, password=form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.email)
    return Token(access_token=access_token)


# ---------------------------------------------------------------------------
# GET /auth/me  — Retrieve the currently authenticated user
# ---------------------------------------------------------------------------
@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve the currently authenticated user",
)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Return the profile of the user identified by the bearer token.
    """
    return current_user
