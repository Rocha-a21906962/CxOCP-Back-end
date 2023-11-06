from typing import List
from models import Process

db = {
    1: Process(id=1, name="Process 1", description="Description 1"),
    2: Process(id=2, name="Process 2", description="Description 2"),
    3: Process(id=3, name="Process 3", description="Description 3")
}


def retrieve_data() -> List[Process]:
    return list(db.values())
