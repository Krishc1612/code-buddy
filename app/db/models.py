from sqlalchemy import Column, ForeignKey, String, DateTime, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
# there are libraries that can detect the language of the piece of code.
from uuid import uuid4, UUID
from datetime import datetime
from enum import Enum

class Sender(str, Enum): # for implementation of Enum we have to do this.
    USER = "user"
    ASSISTANT = "assistant"

class Mode(str, Enum):
    GENERAL = "general"
    PROFESSOR = "professor"
    COLLEGE_BUDDY = "college_buddy"
    ROASTER = "roaster"

class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = "users"

    # id : Mapped[int] = mapped_column(primary_key=True) needs to be a random uuid
    id : Mapped[UUID] = mapped_column(primary_key = True, default = uuid4)
    # "default" here is used as,
    # in case no uuid is provided, create a uuid4 an assign to the object 
    # UUID is an object of class uuid here

    # username : Mapped[str] = mapped_column(String(30)) needs to be a string of not more than
    # certain length
    username : Mapped[str] = mapped_column(String(20), nullable=False)

    # password : need to be hashed when stored inside the database
    password : Mapped[str] = mapped_column(nullable = False)
    # fixing length of password here is harmful as we don't actually know the length of hashed ones.

    # email -> needs to be required.
    email : Mapped[str] = mapped_column(unique = True, nullable = False)

    chats : Mapped[list["Chats"]] = relationship(back_populates = "user")
    # the above statement is not database level but python level that is it establishes relation 
    # between Chats object and Users object.

class Chats(Base):
    __tablename__ = "chats"

    # id
    id : Mapped[UUID] = mapped_column(primary_key = True, default = uuid4)
    # name 
    name : Mapped[str] = mapped_column(String(30), default = "New Chat")
    # mode of assistant
    mode : Mapped[Mode] = mapped_column(SQLEnum(Mode), default = Mode.GENERAL)
    # created_at --> to sort based on latest chats
    created_at : Mapped[datetime] = mapped_column(default = datetime.utcnow)
    # user_id --> foreign key, a relation to map with users table
    user_id : Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    # relations
    user : Mapped["Users"] = relationship(back_populates = "chats")
    messages : Mapped[list["Messages"]] = relationship(back_populates = "chat")

class Messages(Base):
    __tablename__ = "messages" # convention to name the table as a singular

    # id --> needs to be a uuid
    id : Mapped[UUID] = mapped_column(primary_key = True, default = uuid4)
    # content --> in markdown text (can be later broken into segments)
    content : Mapped[str] = mapped_column(Text, nullable = False) # note : text is not python type.
    # mode --> who did the message? User or mode assistant?
    sender : Mapped[Sender] = mapped_column(SQLEnum(Sender), default = Sender.USER)
    # created_at --> message creation details 
    created_at : Mapped[datetime] = mapped_column(default = datetime.utcnow)
    # chat_id --> foreign key, a relation to map with chats table.
    chat_id : Mapped[UUID] = mapped_column(ForeignKey("chats.id"))

    #relations
    chat : Mapped["Chats"] = relationship(back_populates = "messages")