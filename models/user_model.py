from datetime import datetime
from pydantic import EmailStr
from typing import Optional
from uuid import UUID, uuid4


class User:
    def __init__(
            self,
            email: EmailStr,
            username: str,
            hashed_password: str,
            id: UUID = None,
            first_name: Optional[str] = None,
            last_name: Optional[str] = None,
            disabled: Optional[bool] = None,
    ):
        self.id = id or uuid4()
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.first_name = first_name
        self.last_name = last_name
        self.disabled = disabled

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def __str__(self) -> str:
        return self.email

    def __hash__(self) -> int:
        return hash(self.email)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, User):
            return self.email == other.email
        return False

    @property
    def created(self) -> datetime:
        return self.id.time

    @classmethod
    async def by_attribute(cls, attribute_type: str, value: str, container):
        if attribute_type not in ["email", "username", "id"]:
            raise ValueError("Invalid attribute_type. Use 'email', 'username', or 'id'.")

        query = f"SELECT * FROM c WHERE c.{attribute_type} = '{value}'"
        result = container.query_items(query=query, enable_cross_partition_query=True)
        items = list(result)

        if items:
            return cls(
                id=items[0]["id"],
                username=items[0]["username"],
                email=items[0]["email"],
                hashed_password=items[0]["hashed_password"],
                first_name=items[0]["first_name"],
                last_name=items[0]["last_name"],
                disabled=items[0]["disabled"],
            )
        return None

    def to_dict(self):
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "disabled": self.disabled
        }

    @classmethod
    async def save(self, container, user_data):
        container.create_item(user_data.to_dict())
