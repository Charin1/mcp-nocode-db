from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    username: EmailStr
    role: str = "viewer" # Default role
    disabled: bool = False

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str