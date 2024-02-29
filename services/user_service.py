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
        return user_instance
