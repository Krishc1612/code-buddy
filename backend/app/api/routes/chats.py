from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user
from app.core.response_parser import ParsedResponse
from app.db.database import get_async_session
from app.schemas.chats import ChatCreate, ChatRead
from app.schemas.messages import MessageCreate
from app.schemas.users import UserResponse
from app.services.chats_service import get_chats, get_response, make_chat, read_chat_msgs, remove_chat

router = APIRouter(
    prefix = "/chats"
)

@router.post("/create")
async def create_new_chat(
    chat_info : ChatCreate,
    user : UserResponse = Depends(get_current_user),
    db : AsyncSession = Depends(get_async_session)
) -> ChatRead:
    """
        Creates a new chat with the info:
            1. Name
            2. Mode (general, college_buddy, roaster, professor)
    """
    return await make_chat(
        db = db,
        user_id = user.id,
        chat_info = chat_info
    )

@router.get("/all")
async def get_all_user_chats(
    user : UserResponse = Depends(get_current_user),
    db : AsyncSession = Depends(get_async_session)
) -> List[ChatRead]:
    """
        Fetches all the chats of the user.
    """
    return await get_chats(
        db = db,
        user_id = user.id
    )

@router.post("/{chat_id}/send")
async def send_user_msg(
    chat_id : UUID,
    msg : MessageCreate,
    db : AsyncSession = Depends(get_async_session),
    user : UserResponse = Depends(get_current_user)
) -> ParsedResponse:
    """
        Sends user request to the LLM,
        and generates parsed response as per the request.
    """
    return await get_response(
        db = db,
        content = msg,
        chat_id = chat_id,
        user_id = user.id
    )

@router.delete("/{chat_id}/delete")
async def delete_user_chat(
    chat_id : UUID,
    db : AsyncSession = Depends(get_async_session),
    user : UserResponse = Depends(get_current_user)
):
    """
        Deletes the user's chat,
        along with the messages in it.
    """
    return await remove_chat(
        db = db,
        chat_id = chat_id,
        user_id = user.id
    )

@router.get("/{chat_id}/messages")
async def get_chat_msgs(
    chat_id : UUID,
    db : AsyncSession = Depends(get_async_session),
    user : UserResponse = Depends(get_current_user)
):
    return await read_chat_msgs(
        db = db,
        chat_id = chat_id,
        user_id = user.id
    )