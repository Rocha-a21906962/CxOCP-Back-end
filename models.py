from pydantic import BaseModel


class Process(BaseModel):
    id: int
    name: str
    description: str
