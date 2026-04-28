from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.infrastructure.db.repositories.conversation_repository import ConversationRepository
from app.schemas.catalog_item import CatalogItemCreate, CatalogItemResponse, CatalogItemUpdate

router = APIRouter()


@router.get("/", response_model=List[CatalogItemResponse])
async def list_products(
    account_id: str = Query(..., min_length=1),
    include_inactive: bool = Query(default=True),
):
    repo = ConversationRepository()
    return repo.list_catalog_items(account_id=account_id, include_inactive=include_inactive)


@router.get("/{item_id}", response_model=CatalogItemResponse)
async def get_product(item_id: str, account_id: str = Query(..., min_length=1)):
    repo = ConversationRepository()
    item = repo.get_catalog_item(account_id=account_id, item_id=item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Item de catalogo no encontrado")

    return item


@router.post("/", response_model=CatalogItemResponse, status_code=201)
async def create_product(payload: CatalogItemCreate):
    repo = ConversationRepository()
    item = repo.create_catalog_item(payload.model_dump())

    if not item:
        raise HTTPException(status_code=400, detail="No fue posible crear el item de catalogo")

    return item


@router.put("/{item_id}", response_model=CatalogItemResponse)
async def update_product(item_id: str, account_id: str, payload: CatalogItemUpdate):
    repo = ConversationRepository()
    item = repo.update_catalog_item(
        account_id=account_id,
        item_id=item_id,
        payload=payload.model_dump(),
    )

    if not item:
        raise HTTPException(status_code=404, detail="No fue posible actualizar el item de catalogo")

    return item
