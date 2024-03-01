from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any
from services.user_service import UserService

auth_router = APIRouter()

@auth_router.post('/login', summary="Create access and refresh tokens for user")
async def login(form_data: OAuth2PasswordRequestForm = Depends())-> Any:
    user = await UserService.authenticate_user(form_data.username, form_data.password)