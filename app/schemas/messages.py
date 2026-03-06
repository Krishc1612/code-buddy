from pydantic import BaseModel
from app.db.models import Sender
from uuid import UUID
from datetime import datetime

class MessageSend(BaseModel):
    content : str

class MessageRead(BaseModel):
    id : UUID
    sender : Sender
    content : str
    created_at : datetime
    
    model_config = {"from_attributes": True}