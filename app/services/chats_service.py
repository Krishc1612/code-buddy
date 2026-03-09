import os
from uuid import UUID
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.llm_client import generate_response
from app.core.prompt_builder import get_system_message
from app.core.response_parser import ParsedResponse, parse_response
from app.db.crud import create_chat, create_message, delete_chat, get_chat_by_ids, get_chat_messages, get_user_chats, update_chat
from app.schemas.chats import ChatCreate, ChatRead, ChatUpdate
from app.schemas.messages import MessageCreate
from app.services.memory_service import get_chat_context
from typing import List, Dict

load_dotenv()

CONTEXT_MESSAGE_LIMIT = int(os.getenv("CONTEXT_MESSAGE_LIMIT", 10))

def get_response(
    db : Session,
    content : MessageCreate, 
    chat_id : UUID,
    user_id : UUID,
) -> ParsedResponse:
    chat = get_chat_by_ids(
        db = db,
        chat_id = chat_id,
        user_id = user_id
    )

    if not chat:
        raise HTTPException(status_code = 404, detail = f"Chat not found for user {user_id}")
    
    create_message(
        db = db,
        chat_id = chat.id,
        content = content.content,
        sender = "user"
    )

    request_context = get_chat_context(
        db = db,
        chat_id = chat.id,
        n = CONTEXT_MESSAGE_LIMIT
    )

    sys_prompt = get_system_message(chat.mode)

    response = generate_response(
        request = request_context, 
        sys_prompt = sys_prompt
    )

    create_message(
        db = db,
        chat_id = chat.id,
        content = response,
        sender = "assistant"
    )

    return parse_response(response, mode = chat.mode)
# still not returning response metadata here, we might need it when we actually show time-stamps for each message. This function simply returns ParsedResponse to the handler.

def make_chat(
    db : Session,
    user_id : UUID,
    chat_info : ChatCreate
) -> ChatRead :
    db_chat = create_chat(
        db = db,
        chat_name = chat_info.name,
        mode = chat_info.mode,
        user_id = user_id
    )

    return ChatRead.model_validate(db_chat)

def get_chats(
    db : Session,
    user_id : UUID
) -> List[ChatRead]:
    db_user_chats = get_user_chats(
        db = db,
        user_id = user_id
    )

    return [ChatRead.model_validate(chat) for chat in db_user_chats]

def remove_chat(
    db : Session,
    chat_id : UUID,
    user_id : UUID
) -> Dict:
    chat = get_chat_by_ids(
        db = db,
        chat_id = chat_id,
        user_id = user_id
    )

    if not chat:
        raise HTTPException(
            status_code = 404, 
            detail = f"Chat not found for user {user_id}"
        )
    
    if not delete_chat(
        db = db,
        user_id = chat.user_id,
        chat_id = chat.id
    ):
        raise HTTPException(
            status_code = 500, 
            detail = "Internal Server error."
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

def read_chat_msgs(
    db : Session,
    chat_id : UUID,
    user_id : UUID
):  
    db_chat = get_chat_by_ids(
        db = db,
        chat_id = chat_id,
        user_id = user_id
    )

    if not db_chat:
        raise HTTPException(
            status_code = 404, 
            detail = f"Chat not found for user {user_id}"
        )
    
    unparsed_msgs = get_chat_messages(
        db = db,
        chat_id = db_chat.id
    )

    parsed_msgs = []
    for msg in unparsed_msgs:
        if msg["role"] == "assistant":
            msg = {**msg, "content" : parse_response(msg["content"], db_chat.mode)}
            # the above syntax means create a new dictionary with the following key's value overridden to the mentioned value.
        parsed_msgs.append(msg)

    return parsed_msgs

# Note: Attention! the above function's output validation schema cannot be List[ParsedResponse]. Why? Because user message (stored) cannot be classified in that schema. Temporarily not defining the output validation schema here.