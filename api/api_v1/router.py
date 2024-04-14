from fastapi import APIRouter
from api.api_v1.endpoints.user import user_router
from api.api_v1.endpoints.chat import chat_router
from api.api_v1.endpoints.process import process_router
from auth.jwt import auth_router

router = APIRouter()


router.include_router(user_router, prefix="/users", tags=["users"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(process_router, prefix="/process", tags=["processes"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])