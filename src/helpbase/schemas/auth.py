"""Auth-related Pydantic schemas."""

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user in responses."""

    id: str
    email: str
    full_name: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenData(BaseModel):
    """Schema for JWT token payload."""

    sub: str  # user id
    email: str
