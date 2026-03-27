from fastapi import APIRouter
from app.infrastructure.db.repositories.conversation_repository import ConversationRepository
from typing import Dict

router = APIRouter()

@router.get("/kpis", response_model=Dict[str, str])
async def get_dashboard_kpis():
    """Endpoint para obtener los indicadores KPI del dashboard en tiempo real."""
    repo = ConversationRepository()
    return repo.get_kpis()
