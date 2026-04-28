from fastapi import APIRouter
from app.infrastructure.db.repositories.conversation_repository import ConversationRepository
from typing import List, Any
from typing import Optional

router = APIRouter()

@router.get("/", response_model=List[Any])
async def list_conversations(account_id: Optional[str] = None):
    """Generar un endpoint privado para obtener todas las conversaciones Whatsapp."""
    repo = ConversationRepository()
    if account_id:
        return repo.get_conversations_by_account(account_id)
    return repo.get_all_conversations()
