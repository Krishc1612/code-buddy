import os
from uuid import UUID
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.db.crud import get_last_messages

load_dotenv()

def get_chat_context(db: Session, chat_id: UUID):
    orm_context = get_last_messages(
        db = db,
        chat_id = chat_id,
        n = int(os.getenv("CONTEXT_MESSAGE_LIMIT"))
    )

    chat_context = [
        {"role": m.role, "content": m.content}
        for m in orm_context
    ]

    return chat_context