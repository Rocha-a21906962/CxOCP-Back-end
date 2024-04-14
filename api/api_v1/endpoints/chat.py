from fastapi import APIRouter, Depends, HTTPException
import openai
from openai import OpenAI
from api.dependencies.user_dependencies import get_current_user
from models.chat_model import ChatRequest, ChatResponse
from models.user_model import User


chat_router = APIRouter()

@chat_router.post("/", summary="Chat with the AI", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
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