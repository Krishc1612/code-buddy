import os
from uuid import UUID
from fastapi.concurrency import run_in_threadpool
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession 
from app.db.crud import get_last_messages, get_msg_by_id
from app.rag_chat.retrieve import retrieve_similar_chunks
from typing import List, Dict

load_dotenv()

async def get_chat_context(
    db: AsyncSession, 
    chat_id: UUID,
    query : str
):
    orm_context = await get_last_messages(
        db = db,
        chat_id = chat_id,
        n = int(os.getenv("CONTEXT_MESSAGE_LIMIT"))
    )

    context_window = [
        {
            "id" : str(m.id),
            "role" : m.sender,
            "content" : m.content
        }
        for m in orm_context
    ]

    # Rag retrieval
    similar_chunks = await run_in_threadpool( 
        retrieve_similar_chunks,
        query,
        str(chat_id),
        k = 3
    )
    # by retrieving chunks and manipulating them makes sure that user msg and assistant msg are paired together and are removed or kept together.

    # Choosing out the messages in both rag_context and context_window
    recent_ids = {msg["id"] for msg in context_window}

    filtered_chunks = [
        chunk
        for chunk in similar_chunks
        if chunk["user_msg_id"] not in recent_ids and chunk["assistant_msg_id"] not in recent_ids
    ]

    rag_context = await parse_chunks(db = db, chunks = filtered_chunks) # this part was implemented later
 
    # Merging filtered rag and context_window to generate a new context
    final_context = rag_context + context_window

    return [
        {
            "role" : msg["role"],
            "content" : msg["content"]
        }
        for msg in final_context
    ]

async def parse_chunks(
    db : AsyncSession,
    chunks : List[Dict]
) :
    msgs = []
    for data in chunks:
        user_msg_id = UUID(data["user_msg_id"])
        user_msg = await get_msg_by_id(db = db, msg_id = user_msg_id)
        msgs.append(
            {
                "id" : data["user_msg_id"],
                "role" : "user",
                "content" : user_msg.content
            }
        )

        assistant_msg_id = UUID(data["assistant_msg_id"])
        assistant_msg = await get_msg_by_id(db = db, msg_id = assistant_msg_id)
        msgs.append(
            {
                "id" : data["assistant_msg_id"],
                "role" : "assistant",
                "content" : assistant_msg.content
            }
        )

    return msgs
# rather than pasing it manually, just decided to fetch the content again as the value of k here is small.