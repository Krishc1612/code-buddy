from typing import Optional
from pydantic import BaseModel
from app.db.models import Mode
from uuid import uuid4, UUID
from datetime import datetime

class ChatCreate(BaseModel):
    # id : Optional[UUID] = None  while creating chat, user won't provide the details like id
    name : Optional[str] = None
    mode : Optional[Mode] = None # don't worry user will send a string, and pydantic converts it to ENUM. But client has to send it in all lower case, else pydantic will raise an error.
    # created_at : Optional[datetime] = None
    # user_id : UUID --> now, user_id is mandatory while making a user then why do we don't include
    # it here? Answer is, that these schemas are entirely for request "bodies". Also note that client actually sends user_id indirectly through signed tokens which are verified back in backend and then user_id is extracted from it. But again tokens are not part of request body.

# class ChatCreated(BaseModel): do we create a schema for this too? No, because we can use a simple chat read schema for that

class ChatRead(BaseModel):
    id : UUID 
    name : str
    mode : Mode
    created_at : datetime # all of these would be needed when chat's metadata is needed.

    model_config = {"from_attributes": True}  # allow creating ChatRead from ORM objects or other attribute-based objects (Pydantic v2 equivalent of orm_mode)

class ChatUpdate(BaseModel):
    name : Optional[str] = None # client might just "unname" the chat to set it to default name.
    mode : Optional[Mode] = None