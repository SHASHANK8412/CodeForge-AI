from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=3)
    password: str = Field(min_length=6)


class UserLoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6)


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1)


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_preview: str
    raw_key: Optional[str] = None
    created_at: str
