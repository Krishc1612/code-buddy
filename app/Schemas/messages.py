from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.db.models import Sender   # enum containing USER and ASSISTANT


class MessageCreate(BaseModel):
    content: str        # text message sent by the user
    chat_id: UUID       # chat where the message belongs

    # client only sends these two fields
    # backend automatically adds sender and created_at


class MessageResponse(BaseModel):
    id: UUID            # unique message id generated in DB
    content: str        # actual message text
    sender: Sender      # USER or ASSISTANT
    created_at: datetime # time message was created

    class Config:
        from_attributes = True
        # allows returning SQLAlchemy message object directly from routes