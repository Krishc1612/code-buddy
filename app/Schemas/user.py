from pydantic import BaseModel, EmailStr,Field
from uuid import UUID
from typing import Optional


class UserCreate(BaseModel):
    username : str = Field(
        min_length = 3,
        max_length = 20,
        pattern = "^[a-zA-Z0-9_]+$"
    )      # username chosen by the user during registration
    email: EmailStr      # validates that the email format is correct
    password : str = Field(
        min_length = 8,
        max_length = 10
    )        # raw password sent by client (later hashed before saving)


class UserLogin(BaseModel):
    email: EmailStr      # user logs in using email
    password: str        # password used to authenticate


class UserResponse(BaseModel):
    id: UUID             # unique user id generated in database
    username: str        # username stored in DB
    email: EmailStr      # email stored in DB

    class Config:
        from_attributes = True
        # allows SQLAlchemy user object → automatically converted to this schema
        # example: returning `user` from DB automatically becomes UserResponse


class UserUpdate(BaseModel):
    username: Optional[str] = Field(
    default=None,
    min_length=3,
    max_length=20,
    pattern="^[a-zA-Z0-9_]+$"
)  # user can optionally update username
    email: Optional[EmailStr] = None # user can optionally update email