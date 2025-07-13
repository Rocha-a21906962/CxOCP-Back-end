from fastapi import APIRouter, Depends, HTTPException
from api.dependencies.user_dependencies import get_current_user
from core.config import Settings
from models.chat_model import ChatRequest, ChatResponse
from models.user_model import User
from services.neo4j_rag import Neo4jRAGService

chat_router = APIRouter()

settings = Settings()
rag_service = Neo4jRAGService()

@chat_router.post("/", summary="Chat with the AI over the Graph DB", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    question = request.message

    try:
        # Use your RAG service to process the question and get an answer
        answer = rag_service.process_question(question)
        return ChatResponse(role="assistant", content=answer)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))