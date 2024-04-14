from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ProcessCreate(BaseModel):
    title: str = Field(..., title="Title", max_length=55, min_length=1)
    content: str = Field(..., title="content", max_length=11550, min_length=1)
    status: Optional[bool] = False

class ProcessUpdate(BaseModel):
    title: Optional[str] = Field(None, title="Title", max_length=55, min_length=1)
    content: Optional[str] = Field(None, title="content", max_length=11550, min_length=1)
    status: Optional[bool] = False
    
class ProcessOut(BaseModel):
    id: UUID
    status: bool
    title: str
    content: str
    created_at: datetime
    updated_at: datetime