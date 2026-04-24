from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from rog.app.core.database import get_db
from rog.app.schemas.auth import Token, UserCreate, UserLogin
from rog.app.services.auth_service import authenticate_user, create_access_token, register_user

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> dict:
    try:
        user = register_user(db=db, email=str(payload.email).lower(), password=payload.password, full_name=payload.full_name)
    except ValueError as e:
        if str(e) == "email_already_registered":
            raise HTTPException(status_code=400, detail="Email already registered")
        raise
    return {"id": str(user.id), "email": user.email, "full_name": user.full_name, "is_active": user.is_active}


@router.post("/login", response_model=Token)
def login(request: Request, payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    user = authenticate_user(db=db, email=str(payload.email).lower(), password=payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    settings = request.app.state.settings
    token = create_access_token(
        subject=str(user.id),
        secret_key=settings.secret_key,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.access_token_expire_minutes,
    )
    return Token(access_token=token)

