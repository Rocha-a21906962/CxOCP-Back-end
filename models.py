from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    role: str
    content: str

class Process(BaseModel):
    id: int
    name: str
    description: str
