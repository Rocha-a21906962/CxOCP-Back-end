import csv
from fastapi import APIRouter, Depends, HTTPException
import openai
from openai import OpenAI
from api.dependencies.user_dependencies import get_current_user
from models.chat_model import ChatRequest, ChatResponse
from models.user_model import User


chat_router = APIRouter()

def read_business_process_from_csv(csv_file_path):
    """Read the business process from the CSV file and return it as a formatted string."""
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        process_data = [
            f"Time: {row['time'][-8:-3]}, Actor: {row['actor']}, Action: {row['action']}, Description: {row['description']}"
            for row in reader
        ]
    return "\n".join(process_data)

@chat_router.post("/", summary="Chat with the AI", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):

    csv_file = "pizza_business_process.csv"
    process_data = read_business_process_from_csv(csv_file)

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Business Executive ChatBot. And you help with data mining."},
                {"role": "user", "content": f"Please keep in mind the following business process: \"\"\"{process_data}\"\"\". It is a business process for a pizza delivery."},
                {"role": "user", "content": request.message},
            ],
            temperature=0
        )

        response_message = response.choices[0].message.content

        print("OpenAI Response:", response_message)  # Print the entire response for debugging

        return ChatResponse(role="assistant", content=response_message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))