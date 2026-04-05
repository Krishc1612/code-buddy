from uuid import UUID
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.llm_client import generate_response
from app.core.prompt_builder import get_system_message
from app.core.response_parser import ParsedResponse, parse_response
from app.db.crud import create_chat, create_message, delete_chat, get_chat_by_ids, get_chat_messages, get_user_chats, update_chat
from app.db.models import Sender
from app.schemas.chats import ChatCreate, ChatRead, ChatUpdate
from app.schemas.messages import MessageCreate, MessageResponse
from app.services.memory_service import get_chat_context
from app.rag_chat.ingest import ingest_chunk
from typing import List, Dict

async def get_response(
    db : AsyncSession,
    content : MessageCreate, 
    chat_id : UUID,
    user_id : UUID,
) -> ParsedResponse:
    chat = await get_chat_by_ids(
        db = db,
        chat_id = chat_id,
        user_id = user_id
    )

    if not chat:
        raise HTTPException(status_code = 404, detail = f"Chat not found for user {user_id}")
    
    user_msg = await create_message(
        db = db,
        chat_id = chat.id,
        content = content.content,
        sender = Sender.USER
    )

    request_context = await get_chat_context(
        db = db,
        chat_id = chat.id,
        query = content.content
    )

    sys_prompt = get_system_message(chat.mode)

    try :
        response = generate_response(
            request = request_context, 
            sys_prompt = sys_prompt
        )

        assistant_msg = await create_message(
            db = db,
            chat_id = chat.id,
            content = response,
            sender = Sender.ASSISTANT
        )


        await run_in_threadpool(
            ingest_chunk,
            MessageResponse.model_validate(user_msg),
            MessageResponse.model_validate(assistant_msg),
            str(chat.id)
        )

        return parse_response(response, mode = chat.mode)
    # still not returning response metadata here, we might need it when we actually show time-stamps for each message. This function simply returns ParsedResponse to the handler.
    except KeyError:
        assistant_msg = await create_message(
            db = db,
            chat_id = chat.id,
            content = "⚠️ I'm currently unavailable due to high load. Please try again.",
            sender = Sender.ASSISTANT
        )

        return assistant_msg.content

async def make_chat( # there won't be any get_current_user dependency injection here.
    db : AsyncSession,
    user_id : UUID,
    chat_info : ChatCreate
) -> ChatRead :
    db_chat = await create_chat(
        db = db,
        chat_name = chat_info.name,
        mode = chat_info.mode,
        user_id = user_id
    )

    return ChatRead.model_validate(db_chat) # converts ORM Model -> Pydantic object. Then fastapi returns JSON by further converting it.
    # the Class config or model_config comes in use here.

async def get_chats(
    db : AsyncSession,
    user_id : UUID
) -> List[ChatRead]:
    db_user_chats = await get_user_chats(
        db = db,
        user_id = user_id
    )

    return [ChatRead.model_validate(chat) for chat in db_user_chats]

async def remove_chat(
    db : AsyncSession,
    chat_id : UUID,
    user_id : UUID
) -> Dict:
    chat = await get_chat_by_ids(
        db = db,
        chat_id = chat_id,
        user_id = user_id
    )

    if not chat:
        raise HTTPException(
            status_code = 404, 
            detail = f"Chat not found for user {user_id}"
        )
    
    deleted = await delete_chat(
        db = db,
        user_id = chat.user_id,
        chat_id = chat.id
    )

    if not deleted:
        raise HTTPException(
            status_code = 500,
            detail = f"Failed to delete the chat {chat.id}"
        )
    
    return {"message" : f"Chat deleted with chat_id {chat.id}"}

# def change_mode_or_name( <-- check this out. It has too many ifs and else
#     db : Session,
#     chat_id : UUID,
#     user_id : UUID,
#     new_chat : ChatUpdate
# ) -> ChatRead :
#     chat = get_chat_by_ids(
#         db = db,
#         chat_id = chat_id,
#         user_id = user_id
#     )

#     if not chat:
#         raise HTTPException(
#             status_code = 404, 
#             detail = f"Chat not found for user f{user_id}"
#         )
    
#     updates = new_chat.model_dump(exclude_unset = True) # This excludes any field that is not set.

async def read_chat_msgs(
    db : AsyncSession,
    chat_id : UUID,
    user_id : UUID
):  
    db_chat = await get_chat_by_ids(
        db = db,
        chat_id = chat_id,
        user_id = user_id
    )

    if not db_chat:
        raise HTTPException(
            status_code = 404, 
            detail = f"Chat not found for user {user_id}"
        )
    
    unparsed_msgs = await get_chat_messages(
        db = db,
        chat_id = db_chat.id
    )

    parsed_msgs = []
    for msg in unparsed_msgs:
        if msg.sender == Sender.ASSISTANT:
            content = parse_response(msg.content, db_chat.mode)
        else:
            content = msg.content
        
        parsed_msgs.append({
            "id" : msg.id,
            "sender" : msg.sender,
            "content" : content,
            "created_at" : msg.created_at
        })

    return parsed_msgs

# Note: Attention! the above function's output validation schema cannot be List[ParsedResponse]. Why? Because user message (stored) cannot be classified in that schema. Temporarily not defining the output validation schema here.