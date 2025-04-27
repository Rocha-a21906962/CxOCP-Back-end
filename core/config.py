from typing import List
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):

    PROJECT_NAME: str = "CxOCP"
    API_V1_STR: str = "/api/v1"
    OPENAI_ORG_ID: str = os.getenv('OPENAI_ORG_ID')
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY')
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_REFRESH_SECRET_KEY: str = os.getenv("JWT_REFRESH_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    COSMOS_DB: str = os.getenv("COSMOS_DB")
    COSMOS_DB_URI: str = os.getenv("COSMOS_DB_URI")
    COSMOS_DB_KEY: str = os.getenv("COSMOS_DB_KEY")
    COSMOS_DB_CONTAINER: str = os.getenv("COSMOS_DB_CONTAINER")
    COSMOS_DB_CONTAINER2: str = os.getenv("COSMOS_DB_CONTAINER2")
    AZURE_STORAGE_CONNECTION_STRING: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    AZURE_STORAGE_CONTAINER_NAME: str = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
    class Config:
        case_sensitive = True
