import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.core.config import settings
from app.services.rag_service import query_rag
from app.services.chroma_service import clear_vectorstore, get_vectorstore

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the sender, either 'user' or 'assistant'.")
    content: str = Field(..., description="Content of the message.")

class ChatRequest(BaseModel):
    question: str = Field(..., description="The question to ask about the PDF.")
    history: List[ChatMessage] = Field(default=[], description="The chat history.")

@router.post("/chat")
async def chat_endpoint(payload: ChatRequest):
    """
    Submits a query to the RAG service to search the uploaded PDF context
    and return an answer.
    """
    # Validation: Empty question
    question = payload.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty."
        )
        
    # Standardize history format for the RAG service
    history_list = [{"role": msg.role, "content": msg.content} for msg in payload.history]
    
    try:
        logger.info(f"Received query: '{question}' with history length {len(history_list)}")
        answer = query_rag(question, history_list)
        return {"answer": answer}
        
    except ValueError as ve:
        # e.g., if no PDF has been uploaded yet
        logger.warning(f"Validation error in chat: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error answering chat query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while answering your question: {str(e)}"
        )

@router.delete("/clear")
async def clear_database():
    """
    Deletes the Chroma database and clears any uploaded files.
    """
    try:
        logger.info("Request received to clear database and uploaded PDFs.")
        clear_vectorstore()
        return {"message": "Database and uploaded files cleared successfully."}
    except Exception as e:
        logger.error(f"Failed to clear database: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear database: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    System health check. Inspects configurations and vectorstore status.
    """
    api_key_configured = bool(settings.GROK_API_KEY and settings.GROK_API_KEY != "your_grok_api_key_here")
    vectorstore_active = get_vectorstore() is not None
    
    return {
        "status": "healthy",
        "api_key_configured": api_key_configured,
        "pdf_uploaded": vectorstore_active,
        "model_name": settings.MODEL_NAME
    }
