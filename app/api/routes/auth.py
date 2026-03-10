from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# from app.api.dependencies import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.crud import create_user, get_user_by_email
from app.db.database import get_async_session
from app.schemas.users import UserCreate, UserLogin, UserResponse

router = APIRouter(
    prefix = "/api/auth"
)

@router.post("/register")
async def register_user(
    user_info : UserCreate,
    db : AsyncSession = Depends(get_async_session)
) -> UserResponse:
    db_user = await get_user_by_email(
        db = db,
        email = user_info.email
    )

    if db_user:
        raise HTTPException(status_code = 409, detail = "User already exists")
    
    password_hashed = hash_password(user_info.password)

    new_user = await create_user(
        db = db,
        username = user_info.username,
        password_hash = password_hashed,
        email = user_info.email
    )

    return UserResponse.model_validate(new_user)

@router.post("/login")
async def login_user(
    user_info : UserLogin,
    db : AsyncSession = Depends(get_async_session)
) -> UserResponse:
    db_user = await get_user_by_email(
        db = db,
        user_id = user_info.email
    )

    if not db_user:
        raise HTTPException(status_code = 401, detail = "Invalid email or password")
    
    verified = verify_password(
        password = user_info.password,
        hashed_password = db_user.password
    )

    if not verified:
        raise HTTPException(status_code = 401, detail = "Invalid email or password")
    
    token = create_access_token(
        { "user_id" : db_user.id }
    )

    return {
        "access_token" : token,
        "token_type" : "bearer"
    }

# @router.get("/logout")
# async def logout_user(
#     user : UserResponse = Depends(get_current_user),
#     db : AsyncSession = Depends(get_async_session)
# ): implementing it later.  