from fastapi import APIRouter, Depends, HTTPException
from app.schemas.quote import QuoteCreate, QuoteResponse
from app.domain.services.quote_service import QuoteService
from app.infrastructure.db.repositories.conversation_repository import ConversationRepository
from typing import List, Any

router = APIRouter()

@router.post("/", response_model=QuoteResponse)
async def create_quote(payload: QuoteCreate):
    service = QuoteService()
    result = await service.create_quote(payload.items)
    return result

@router.get("/recent", response_model=List[Any])
async def list_recent_quotes():
    """Generar un endpoint privado para obtener las últimas cotizaciones con historial."""
    repo = ConversationRepository()
    return repo.get_recent_quotes(limit=15)
