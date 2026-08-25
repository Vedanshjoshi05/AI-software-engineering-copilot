from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserPublic(BaseModel):
    id: str
    name: str
    email: str


class UserProfile(UserPublic):
    avatar: str = ""
    createdAt: datetime | None = None
    updatedAt: datetime | None = None


class RegisterResponse(BaseModel):
    success: bool = True
    message: str = "User registered successfully"
    user: UserPublic


class LoginResponse(BaseModel):
    success: bool = True
    message: str = "Login successful"
    token: str
    user: UserPublic


class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "Logout successful"


class ProfileResponse(BaseModel):
    success: bool = True
    message: str = "User profile retrieved successfully"
    user: UserProfile
