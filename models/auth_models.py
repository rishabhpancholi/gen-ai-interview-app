from pydantic import BaseModel, Field, EmailStr
from typing import Annotated


class CreateUser(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    email: Annotated[EmailStr, Field(min_length=10)]
    password: Annotated[str, Field(min_length=6, max_length=255)]


class LoginUser(BaseModel):
    email: Annotated[EmailStr, Field(min_length=10)]
    password: Annotated[str, Field(min_length=6, max_length=255)]
