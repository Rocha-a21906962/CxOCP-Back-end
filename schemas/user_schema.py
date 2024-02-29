from pydantic import BaseModel, EmailStr, Field

class UserAuth(BaseModel):
    email: EmailStr = Field(..., description="The email of the user")
    username: str = Field(..., min_length=5, max_length=50, description="The username of the user")
    password: str = Field(..., min_length=5, max_length=24, description="The password of the user")