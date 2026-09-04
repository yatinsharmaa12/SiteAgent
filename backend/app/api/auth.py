from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session
from app.core.rate_limit import (
    check_login_rate_limit,
    check_register_rate_limit,
)
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def validate_password_strength(password: str) -> str:
    if not isinstance(password, str):
        raise ValueError("Password must be a string")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if len(password) > 128:
        raise ValueError("Password must be at most 128 characters")
    if not password.strip() or len(password.strip()) < 8:
        raise ValueError("Password must be at least 8 characters")
    return password


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password_strength(value)


@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
    http_request: Request = None,  # type: ignore[assignment]
):
    check_register_rate_limit(http_request)
    try:
        validate_password_strength(request.password)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    existing_user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
    }

@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    http_request: Request = None,  # type: ignore[assignment]
):
    email = getattr(request, "email", None)
    check_login_rate_limit(http_request, email if isinstance(email, str) else None)
    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if not user or not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.post("/token")
def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    http_request: Request = None,  # type: ignore[assignment]
):
    username = getattr(form_data, "username", None)
    check_login_rate_limit(http_request, username if isinstance(username, str) else None)
    user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )

    if not user or not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }