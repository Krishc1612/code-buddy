from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.crud import create_user, fetch_user_details
from app.db.database import get_async_session
from app.schemas.users import UserCreate, UserResponse

router = APIRouter(
    prefix = "/api/auth"
)

@router.post("/register")
async def register_user(
    user_info : UserCreate,
    session : Session = Depends(get_async_session)
):
    db_user = fetch_user_details(
        db = session,
        user_id = user_info.id
    )

    if db_user:
        raise HTTPException(status_code = 409, detail = "User already exists")
    
    password_hashed = hash_password(user_info.password)

    new_user = create_user(
        db = session,
        username = user_info.username,
        password_hash = password_hashed,
        email = user_info.email
    )

    return UserResponse.model_validate(new_user)