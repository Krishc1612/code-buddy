from uuid import UUID
from sqlalchemy.orm import Session # needed for the type hint "Session"
from app.db.models import Chats, Messages, Mode, Sender, Users
# from app.schemas.users import UserCreate

def create_user(db : Session, username : str, email : str, password_hash : str): 
    db_user = Users(**{
        "username" : username,
        "email" : email,
        "password" : password_hash
    }) # could also have mentioned like we specify in function passing, Users(username = username ...)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

# the hashing of password must be done in service layer not in the database layer. As hashing will done before hand it no longer satisfies the schema design of UserCreate as password length is too small in it and hashed passwords are longer. So we have to take separate inputs or create a new Schema UserDBCreate

def fetch_user_details(db : Session, user_id : UUID):
    return (
        db.query(Users.username, Users.email) # if we query whole table it returns ORM object with all columns as attributes but if we mention specific attributes, it would only return those
        .filter(Users.id == user_id) # basically where clause
        .first() # the first actually executes the query and here it would give the first row object corresponding to the model.
    ) 

def fetch_password(db : Session, email : str):
    return (
        db.query(
            Users.email,
            Users.password
        )
        .filter(Users.email == email)
        .first()
    )

def update_user(db : Session, user_id : UUID, username : str):
    # db_user = db.query(
    #     Users.username
    # ).filter(Users.id == user_id).first() not fine, returns an ORM row object which is read only

    db_user = db.get(Users, user_id) # fetching with .get if have the primary key.

    if not db_user:
        return None
    
    db_user.username = username
    db.commit()
    db.refresh(db_user)

    return db_user # no need to sweat here this won't expose user.id to client as there is another layer upon db layer called service layer.

def delete_user(db : Session, user_id : UUID) -> bool:
    db_user = db.get(Users, user_id)

    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()

    return True

def create_chat(db : Session, chat_name : str, mode : Mode, user_id : UUID):
    db_chat = Chats(
        name = chat_name,
        mode = mode,
        user_id = user_id
    )

    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)

    return db_chat

def get_user_chats(db : Session, user_id : UUID):
    return (
        db.query(Chats)
        .filter(Chats.user_id == user_id)
        .order_by(Chats.created_at.desc())
        .all()
    )

def fetch_named_chats(db : Session, user_id : UUID, chat_name : str):
    return (
        db.query(Chats)
        .filter(
            Chats.user_id == user_id,
            Chats.name == chat_name
        )
        .all()
    )

def update_chat(db : Session, user_id : UUID, chat_id : UUID, chat_name : str, mode : Mode):
    db_chat = (
        db.query(Chats)
        .filter(
            Chats.user_id == user_id,
            Chats.id == chat_id
        )
        .first()
    )

    if not db_chat:
        return None
    
    db_chat.name = chat_name 
    db_chat.mode = mode

    db.commit()
    db.refresh(db_chat)

    return db_chat

def delete_chat(db : Session, user_id : UUID, chat_id : UUID):
    db_chat = (
        db.query(Chats)
        .filter(
            Chats.user_id == user_id,
            Chats.id == chat_id
        )
        .first()
    )

    if not db_chat:
        return False
    
    db.delete(db_chat)
    db.commit()

    return True

def create_message(db : Session, chat_id : UUID, content : str, sender : Sender):
    db_message = Messages (
        chat_id = chat_id,
        content = content,
        sender = sender
    )

    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    return db_message

def get_chat_messages(db : Session, chat_id : UUID):
    return (
        db.query(Messages)
        .filter(
            Messages.chat_id == chat_id
        )
        .order_by(Messages.created_at.desc())
        .all()
    )

def get_last_messages(db : Session, chat_id : UUID, n : int):
    return (
        db.query(Messages)
        .filter(
            Messages.chat_id == chat_id
        )
        .order_by(Messages.created_at.desc())
        .limit(n)
        .all()
    )