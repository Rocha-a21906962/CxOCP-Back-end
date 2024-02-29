from fastapi import APIRouter
from api.api_v1.endpoints.user import user_router

router = APIRouter()

router.include_router(user_router, prefix="/users", tags=["users"])