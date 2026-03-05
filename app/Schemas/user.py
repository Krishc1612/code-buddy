from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional


class UserCreate(BaseModel):
    username: str        # username chosen by the user during registration
    email: EmailStr      # validates that the email format is correct
    password: str        # raw password sent by client (later hashed before saving)


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
    username: Optional[str] = None   # user can optionally update username
    email: Optional[EmailStr] = None # user can optionally update email