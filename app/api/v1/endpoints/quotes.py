import os
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from app.schemas.quote import QuoteCreate, QuoteResponse
from app.domain.services.quote_service import QuoteService
from app.infrastructure.db.repositories.conversation_repository import ConversationRepository

router = APIRouter()

@router.post("/", response_model=QuoteResponse)
async def create_quote(payload: QuoteCreate):
    service = QuoteService()
    result = await service.create_quote(payload.items)
    return result

@router.get("/recent", response_model=List[Any])
async def list_recent_quotes(account_id: Optional[str] = None):
    """Generar un endpoint privado para obtener las últimas cotizaciones con historial."""
    repo = ConversationRepository()
    if account_id:
        return repo.get_recent_quotes_by_account(account_id, limit=15)
    return repo.get_recent_quotes(limit=15)


@router.get("/", response_model=List[Any])
async def list_quotes(account_id: str, limit: int = 100):
    """Retorna cotizaciones completas para el dashboard comercial."""
    repo = ConversationRepository()
    return repo.list_quotes_by_account(account_id=account_id, limit=limit)


@router.get("/{quote_id}/pdf")
async def get_quote_pdf(quote_id: str):
    """Permite abrir el PDF asociado a una cotizacion."""
    repo = ConversationRepository()
    pdf_source = repo.get_quote_pdf_source(quote_id)

    if not pdf_source or not pdf_source.get("pdf_url"):
        raise HTTPException(status_code=404, detail="La cotizacion no tiene un PDF asociado.")

    if pdf_source.get("is_remote"):
        return RedirectResponse(url=pdf_source["pdf_url"])

    if not pdf_source.get("exists"):
        raise HTTPException(status_code=404, detail="El archivo PDF no fue encontrado en el servidor.")

    filename = os.path.basename(pdf_source["pdf_url"])
    return FileResponse(path=pdf_source["pdf_url"], media_type="application/pdf", filename=filename)
