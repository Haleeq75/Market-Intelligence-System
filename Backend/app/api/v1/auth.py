"""
app/api/v1/ — All endpoint routers
"""
from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# auth.py
# ─────────────────────────────────────────────────────────────────────────────
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", status_code=201)
async def register(
    body: "UserRegisterRequest",
    db: "DbSession",
):
    from app.database.crud.user import create_user, get_user_by_email
    from app.api.schemas.all import UserResponse
    existing = await get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await create_user(db, email=body.email, password=body.password, full_name=body.full_name)
    return UserResponse.model_validate(user)


@auth_router.post("/token")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: "DbSession" = Depends(),
):
    from app.database.crud.user import get_user_by_email
    from app.core.security import create_access_token, create_refresh_token, verify_password
    from app.api.schemas.all import TokenResponse
    user = await get_user_by_email(db, form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@auth_router.get("/me")
async def me(current_user: "CurrentUser"):
    from app.api.schemas.all import UserResponse
    return UserResponse.model_validate(current_user)
