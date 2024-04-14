from datetime import datetime

from azure.cosmos import CosmosClient
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError

from core.config import Settings
from models.user_model import User
from schemas.auth_schema import TokenPayload
from services.user_service import UserService

settings = Settings()

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", scheme_name="JWT")

async def get_current_user(token: str = Depends(reusable_oauth2)) -> User:

    client = CosmosClient(settings.COSMOS_DB_URI, settings.COSMOS_DB_KEY)
    database = client.get_database_client(settings.COSMOS_DB)
    container = database.get_container_client(settings.COSMOS_DB_CONTAINER)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )

    try:

        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])

        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except(jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = await UserService.get_user_by_id(token_data.sub, container)

    if not User:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user