"""
Authentication routes — equivalent of routes/authRoutes.js + controller/authController.js.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationAppError
from app.core.security import create_access_token, verify_password
from app.models import user as user_model
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    ProfileResponse,
    RegisterRequest,
    RegisterResponse,
    UserProfile,
    UserPublic,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
    summary="Register a new user",
)
async def register(payload: RegisterRequest) -> RegisterResponse:
    existing = await user_model.find_user_by_email(payload.email)
    if existing:
        raise ValidationAppError("User already exists")

    user_doc = await user_model.create_user(
        payload.name, payload.email, payload.password
    )

    return RegisterResponse(
        user=UserPublic(
            id=str(user_doc["_id"]), name=user_doc["name"], email=user_doc["email"]
        )
    )


@router.post("/login", response_model=LoginResponse, summary="Log in and receive a JWT")
async def login(payload: LoginRequest) -> LoginResponse:
    user_doc = await user_model.find_user_by_email(payload.email)
    if not user_doc:
        raise UnauthorizedError("Invalid credentials")

    if not verify_password(payload.password, user_doc.get("password", "")):
        raise UnauthorizedError("Invalid credentials")

    token = create_access_token(str(user_doc["_id"]))

    return LoginResponse(
        token=token,
        user=UserPublic(
            id=str(user_doc["_id"]), name=user_doc["name"], email=user_doc["email"]
        ),
    )


@router.post(
    "/logout", response_model=LogoutResponse, summary="Log out (stateless JWT no-op)"
)
async def logout() -> LogoutResponse:
    return LogoutResponse()


@router.get(
    "/profile", response_model=ProfileResponse, summary="Get the current user's profile"
)
async def get_profile(user_id: str = Depends(get_current_user_id)) -> ProfileResponse:
    user_doc = await user_model.find_user_by_id(user_id)
    if not user_doc:
        raise NotFoundError("User not found")

    return ProfileResponse(
        user=UserProfile(
            id=str(user_doc["_id"]),
            name=user_doc["name"],
            email=user_doc["email"],
            avatar=user_doc.get("avatar", ""),
            createdAt=user_doc.get("createdAt"),
            updatedAt=user_doc.get("updatedAt"),
        )
    )
