from uuid import UUID

from schemas.user_schema import UserAuth
from models2.user_model import User
from core.security import get_password_hash, verify_password

class UserService:
    @staticmethod
    async def create_user(user: UserAuth, container):

        user_instance = User(
            email=user.email,
            username=user.username,
            hashed_password=get_password_hash(user.password)
        )

        await User.save(container, user_instance)
        return user_instance.to_dict()

    @staticmethod
    async def authenticate_user(username: str, password: str, container):

        user = await User.by_username(username, container)

        if not user:
            return None
        if not verify_password(plain_password=password, hashed_password=user.hashed_password):
            return None

        return user

    @staticmethod
    async def get_user_by_id(user_id: UUID):
        user = await User.get(user_id)
        return user.to_dict()
