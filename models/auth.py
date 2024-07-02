from enum import Enum
from pydantic import BaseModel, EmailStr


class Role(str, Enum):
    Admin = "Admin"
    User = "User"
    
    # @classmethod
    # def from_str(cls, value: str):
    #     value_lower = value.lower()
    #     if value_lower == "admin":
    #         return cls.Admin
    #     elif value_lower == "user":
    #         return cls.User
    #     else:
    #         raise ValueError(f"Invalid role: {value}")

class Signup(BaseModel):
    userName: str
    email: EmailStr
    password: str
    role: Role
    # cPassword: str


class Login(BaseModel):
    email: EmailStr
    password: str
