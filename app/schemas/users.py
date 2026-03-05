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

    model_config = {"from_attributes": True} # yet to know what this does

class UserUpdate(BaseModel):
    username : str | None = Field(
        min_length = 3,
        max_length = 20,
        pattern = "^[a-zA-Z0-9_]+$"
    )