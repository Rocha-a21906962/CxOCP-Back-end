import csv

from env import OPENAI_ORG_ID, OPENAI_API_KEY
from models import Process, ChatRequest, ChatResponse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
from openai import OpenAI
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

client = OpenAI(
    organization=OPENAI_ORG_ID,
    api_key=OPENAI_API_KEY
)

@app.get('/')
def hello():
    return {"message": "Hello from Azure Container App!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    def read_business_process_from_csv(csv_file_path):
        """Read the business process from the CSV file and return it as a string."""
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            process_data = [row["Description"] for row in reader]
        return "\n".join(process_data)

    csv_file = "pizza_business_process.csv"
    process_data = read_business_process_from_csv(csv_file)

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Business Executive ChatBot. And you help with data mining."},
                {"role": "user", "content": f"Please keep in mind the following business process: \"\"\"{process_data}\"\"\"."},
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
