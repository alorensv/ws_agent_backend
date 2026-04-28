from fastapi import APIRouter
from app.infrastructure.db.repositories.conversation_repository import ConversationRepository
from typing import Dict
from typing import Optional, List, Any

router = APIRouter()

@router.get("/kpis", response_model=Dict[str, str])
async def get_dashboard_kpis(account_id: Optional[str] = None):
    """Endpoint para obtener los indicadores KPI del dashboard en tiempo real."""
    repo = ConversationRepository()
    if account_id:
        return repo.get_kpis_by_account(account_id)
    return repo.get_kpis()

@router.get("/accounts", response_model=List[Any])
async def list_dashboard_accounts():
    """Retorna cuentas activas para poblar el selector del dashboard."""
    repo = ConversationRepository()
    return repo.get_active_accounts()
