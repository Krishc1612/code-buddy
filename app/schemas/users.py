from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username : str = Field(
        min_length = 3,
        max_length = 20,
        pattern = "^[a-zA-Z0-9_]+$"
    )
    password : str = Field(
        min_length = 8,
        max_length = 10
    )
    email : EmailStr

class UserRead(BaseModel):
    username : str
    email : EmailStr

    model_config = {"from_attributes": True} 
    # What this line does:
    # When we return a SQLAlchemy object from a FastAPI route, FastAPI uses the
    # response_model (a Pydantic model) to validate and serialize the response.

    # However, Pydantic normally expects dictionary-like data for validation.
    # A SQLAlchemy model is an object with attributes (user.id, user.username).

    # By enabling "from_attributes = True", we tell Pydantic that it should read
    # values from object attributes instead of dictionary keys.

    # This allows Pydantic to convert the SQLAlchemy object into a Pydantic model,
    # and FastAPI then serializes that Pydantic model into JSON for the client.           

class UserUpdate(BaseModel):
    username : str | None = Field(
        min_length = 3,
        max_length = 20,
        pattern = "^[a-zA-Z0-9_]+$",
        default = None
    )