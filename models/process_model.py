from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from models.user_model import User

class Process:
    def __init__(
            self,
            id: UUID = None,
            status: bool = False,
            title: str = None,
            content: str = None,
            created_at: datetime = None,
            updated_at: datetime = None,
            owner: Optional[User] = None
            
    ):
        self.id = id or uuid4()
        self.status = status
        self.title = title
        self.content = content
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.owner = owner

    def __repr__(self):
        return f'<Process {self.title}>'
    
    def __str__(self):
        return self.title
    
    def __hash__(self) -> int:
        return hash(self.title)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Process):
            return self.id == other.id
        return False
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'status': self.status,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'owner': self.owner.to_dict() if self.owner else None  # Assuming User has a to_dict method
        }
    
    @classmethod
    async def save(self, container, user_data):
        container.create_item(user_data)
    