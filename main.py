from models import Process, ChatRequest, ChatResponse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
from openai import OpenAI
from typing import List
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

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

openai_org_id = os.getenv("OPENAI_ORG_ID")
openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    organization=openai_org_id,
    api_key=openai_api_key
)

@app.get('/')
def hello():
    return {"message": "Hello from Azure Container App!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Business Man. And you help with data mining."},
                {"role": "user", "content": request.message},
            ],
            temperature=0
        )

        response_message = response.choices[0].message.content

        print("OpenAI Response:", response_message)  # Print the entire response for debugging

        return ChatResponse(role="assistant", content=response_message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/processes/", response_model=List[Process])
async def get_processes():
    # Use the retrieve_data function to retrieve data from the mock database
    processes = retrieve_data()
    return processes


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
