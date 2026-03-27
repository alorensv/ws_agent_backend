from fastapi import APIRouter
from app.infrastructure.db.repositories.conversation_repository import ConversationRepository
from typing import List, Any

router = APIRouter()

@router.get("/", response_model=List[Any])
async def list_conversations():
    """Generar un endpoint privado para obtener todas las conversaciones Whatsapp."""
    repo = ConversationRepository()
    return repo.get_all_conversations()
