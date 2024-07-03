from enum import Enum
from pydantic import BaseModel, EmailStr


class Role(str, Enum):
    Admin = "Admin"
    User = "User"
    

class Signup(BaseModel):
    userName: str
    email: EmailStr
    password: str
    role: Role
    # cPassword: str


class Login(BaseModel):
    email: EmailStr
    password: str
