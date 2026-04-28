from fastapi import APIRouter, HTTPException

from app.infrastructure.db.repositories.conversation_repository import ConversationRepository
from app.schemas.prompt_training import PromptTrainingResponse, PromptTrainingUpdate

router = APIRouter()


@router.get("/{account_id}", response_model=PromptTrainingResponse)
async def get_account_prompt(account_id: str):
    repo = ConversationRepository()
    account = repo.get_account_prompt(account_id)

    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    return account


@router.put("/{account_id}", response_model=PromptTrainingResponse)
async def update_account_prompt(account_id: str, payload: PromptTrainingUpdate):
    repo = ConversationRepository()
    account = repo.update_account_prompt(account_id, payload.system_prompt)

    if not account:
        raise HTTPException(status_code=404, detail="No fue posible actualizar la cuenta")

    return account
