from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.core.security import decode_access_token
from app.db.database import get_async_session
from app.db.crud import fetch_user_details

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login") # the tokenUrl should match the Url at which users will be able to verify the token as their identity. In short from where they can login.
# this line creates a security dependency. It looks for Authorization header in the request headers. FastAPI extracts the JWT token part and returns it (will get to "token" here)
# If the header is missing FastAPI automatically returns 401 Not Authenticated.

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_session) # fetchs the async session 
):
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")

    except JWTError: # the case when decode_access_token might fail (token is malicious)
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = await fetch_user_details(db, user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user