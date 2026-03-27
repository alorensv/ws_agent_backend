from pydantic import BaseModel
from typing import List, Optional

class QuoteItem(BaseModel):
    product_name: str
    quantity: int
    price: Optional[float] = None

class QuoteCreate(BaseModel):
    items: List[QuoteItem]
    client_phone: Optional[str] = None

class QuoteResponse(BaseModel):
    id: int
    total: float
    client_phone: Optional[str] = None
