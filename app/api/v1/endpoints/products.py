from fastapi import APIRouter
from typing import List

router = APIRouter()

@router.get("/")
def get_products():
    return [
        {"id": 1, "name": "Producto A", "price": 10.0},
        {"id": 2, "name": "Producto B", "price": 20.0}
    ]
