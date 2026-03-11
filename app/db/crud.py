from sqlalchemy import select
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession # needed for the type hint "AsyncSession"
from app.db.models import Chats, Messages, Mode, Sender, Users
# from app.schemas.users import UserCreate

async def create_user(
    db : AsyncSession, 
    username : str, 
    email : str, 
    password_hash : str
): 
    db_user = Users(**{
        "username" : username,
        "email" : email,
        "password" : password_hash
    }) # could also have mentioned like we specify in function passing, Users(username = username ...)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user

# the hashing of password must be done in service layer not in the database layer. As hashing will done before hand it no longer satisfies the schema design of UserCreate as password length is too small in it and hashed passwords are longer. So we have to take separate inputs or create a new Schema UserDBCreate

async def fetch_user_details( # 404 if None returned
    db : AsyncSession, 
    user_id : UUID
):
    # return (
    #     db.query(Users.username, Users.email) # if we query whole table it returns ORM object with all columns as attributes but if we mention specific attributes, it would only return those
    #     .filter(Users.id == user_id) # basically where clause
    #     .first() # the first actually executes the query and here it would give the first row object corresponding to the model.
    # ) this is previous code, which was sync this should be commented out so as to not lose the comments made with it which cam be useful for future.

    payload = await db.execute(
        select(Users)
        .where(Users.id == user_id)
    )

    user = payload.scalars().first()

    return user
async def get_user_by_email( # 404 if None returned
    db : AsyncSession, 
    email : str
):
    # return (
    #     db.query(
    #         Users.email,
    #         Users.password
    #     )
    #     .filter(Users.email == email)
    #     .first()
    # )

    payload = await db.execute(
        select(Users) # handler would also need the user id as an access token must be generated out of it.
        .where(Users.email == email)
    )
    # Now there is an interesting way in which .execute returns.
    # It returns,
    # 1. Result [Row(User(...),), Row(User(...),) ...] (in case we requested Model like select(Users))
    # 2. Result [Row(id, password), Row(id, password), ...] (in case we asked for columns (above))
    # Note : In the case when Model is selected there is only one column while later there is two.

    # scalars() can convert 1st one to just [User(...), User(...)] (only first column retrieved)
    # scalars() can convert 2nd one to just [id, id, id ... ] (only first column is retrieved)

    # first() converts the 1st Result to just Row(User(...)). Now, to access column values we must do Row[0].columnName
    # first() converts the 2nd Result to just Row(id, password). Now, to access id column we can directly do, Row.id.

    user = payload.scalars().first() # above reason we used .first here.

    return user 

async def update_user( # raising exception in services if None was returned 
    db : AsyncSession, 
    user_id : UUID, 
    username : str
):
    # db_user = db.query(
    #     Users.username
    # ).filter(Users.id == user_id).first() not fine, returns an ORM row object which is read only

    db_user = await db.execute(
        select(Users)
        .where(Users.id == user_id)
    )# fetching with .get if have the primary key.

    user = db_user.scalars().first()
    # why "scalars()" here? To convert the result to [User(...), User(...), ...]
    # and then .first() to access the first element i.e, User(...)
    # why do all of this? So that the columns can directly be accessed like var.columnName.
    if not user:
        return None
    
    user.username = username # accessing directly by var.columnName
    await db.commit()
    await db.refresh(user)

    return user # no need to sweat here this won't expose user.id to client as there is another layer upon db layer called service layer.

async def delete_user( # raising exception if None returned in services
    db : AsyncSession, 
    user_id : UUID
) -> bool:
    db_user = await db.execute(
        select(Users)
        .where(Users.id == user_id)
    )

    user = db_user.scalars().first()

    if not user:
        return False
    
    await db.delete(user)
    await db.commit()

    return True

async def create_chat(
    db : AsyncSession, 
    chat_name : str, 
    mode : Mode, 
    user_id : UUID
):
    db_chat = Chats(
        name = chat_name,
        mode = mode,
        user_id = user_id
    )

    db.add(db_chat)
    await db.commit()
    await db.refresh(db_chat)

    return db_chat

async def get_chat_by_ids(
    db : AsyncSession, 
    chat_id : UUID, 
    user_id : UUID
):
    db_chat = await db.execute(
        select(Chats)
        .where(Chats.id == chat_id, Chats.user_id == user_id)
    )

    chat = db_chat.scalars().first()

    return chat

async def get_user_chats(
    db : AsyncSession, 
    user_id : UUID
):
    # return (
    #     db.query(Chats)
    #     .filter(Chats.user_id == user_id)
    #     .order_by(Chats.created_at.desc())
    #     .all()
    # )
    db_chats = await db.execute(
        select(Chats)
        .where(Chats.user_id == user_id)
        .order_by(Chats.created_at.desc())
    )

    chats = db_chats.scalars().all()

    return chats

async def fetch_named_chats(
    db : AsyncSession, 
    user_id : UUID, 
    chat_name : str
):
    db_named_chats = await db.execute(
        select(Chats)
        .where(Chats.name == chat_name, Chats.user_id == user_id)
        .order_by(Chats.created_at.desc())
    )

    named_chats = db_named_chats.scalars().all()

    return named_chats

async def update_chat( # fetch chat first
    db : AsyncSession, 
    user_id : UUID, 
    chat_id : UUID, 
    chat_name : str
):
    db_chat = await db.execute(
        select(Chats)
        .where(Chats.user_id == user_id, Chats.id == chat_id)
    )

    chat = db_chat.scalars().first()

    if not chat:
        return None
    
    chat.name = chat_name 
    # chat.mode = mode not implementing this for now.

    await db.commit()
    await db.refresh(chat)

    return chat

async def delete_chat( # fetch chat in service
    db : AsyncSession, 
    user_id : UUID, 
    chat_id : UUID
):
    db_chat = await db.execute(
        select(Chats)
        .where(Chats.user_id == user_id, Chats.id == chat_id)
    )

    chat = db_chat.scalars().first()

    if not chat:
        return False
    
    await db.delete(chat)
    await db.commit()

    return True

async def create_message( # chat must be fetched in service layer to see whether chat belongs to user or even chat exists or not.
    db : AsyncSession, 
    chat_id : UUID, 
    content : str, 
    sender : Sender
):
    db_message = Messages (
        chat_id = chat_id,
        content = content,
        sender = sender
    )

    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)

    return db_message

async def get_chat_messages(
    db : AsyncSession, 
    chat_id : UUID
):
    db_msgs = await db.execute(
        select(Messages)
        .where(Messages.chat_id == chat_id)
        .order_by(Messages.created_at.desc())
    )

    msgs = db_msgs.scalars().all()

    return msgs

async def get_last_messages(
    db : AsyncSession, 
    chat_id : UUID, 
    n : int
):
    db_last_msgs = await db.execute(
        select(Messages)
        .where(Messages.chat_id == chat_id)
        .order_by(Messages.created_at)
        .limit(n)
    )

    last_msgs = db_last_msgs.scalars().all()

    return last_msgs