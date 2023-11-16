from models import Process
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from database import (
    retrieve_data
)

app = FastAPI()

origins = ["http://localhost:3000"]  # FE PORT

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods="*",
    allow_headers="*"
)

@app.get('/')
def hello():
    return {"message": "Hello from Azure Container App!"}

@app.get("/processes/", response_model=List[Process])
async def get_processes():
    # Use the retrieve_data function to retrieve data from the mock database
    processes = retrieve_data()
    return processes


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
