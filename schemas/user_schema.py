from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID


class UserAuth(BaseModel):
    email: EmailStr = Field(..., description="The email of the user")
    username: str = Field(..., min_length=4, max_length=50, description="The username of the user")
    password: str = Field(..., min_length=4, max_length=24, description="The password of the user")


class UserOut(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    disabled: Optional[bool] = False
