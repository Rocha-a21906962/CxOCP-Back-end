import os

from azure.cosmos import CosmosClient
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

from jose import jwt
from pydantic import ValidationError

from api.dependencies.user_dependencies import get_current_user
from core.config import Settings
from core.security import create_access_token, create_refresh_token
from models.user_model import User
from schemas.auth_schema import TokenSchema, TokenPayload
from schemas.user_schema import UserOut
from services.user_service import UserService

settings = Settings()

auth_router = APIRouter()

client = CosmosClient(settings.COSMOS_DB_URI, settings.COSMOS_DB_KEY)
database = client.get_database_client(settings.COSMOS_DB)
container = database.get_container_client(settings.COSMOS_DB_CONTAINER)

@auth_router.post('/login', summary="Login to get an access token", response_description="Access token and refresh token", response_model=TokenSchema)
async def login(username: str = Body(...), password: str = Body(...)) -> Any:
    user = await UserService.authenticate_user(username, password, container=container)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id)
    }

@auth_router.post('/test-token', summary="Test if access token is valid", response_model=UserOut)
async def test_token(user: User = Depends(get_current_user)):
    return user

@auth_router.post('/refresh-token', summary="Refresh access token", response_model=TokenSchema)
async def refresh_token(refresh_token: str = Body(...)):
    try:
        payload = jwt.decode(refresh_token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = await UserService.get_user_by_id(token_data.sub, container=container)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid token for user"
        )

    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id)
    }