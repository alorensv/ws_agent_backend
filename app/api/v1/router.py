from fastapi import APIRouter
from app.api.v1.endpoints import products, quotes, webhook, conversations, dashboard, prompt_training

api_router = APIRouter()

# 1. Endpoint para el catálogo
api_router.include_router(products.router, prefix="/products", tags=["Catálogo"])

# 2. Endpoint para cotizaciones (V2)
api_router.include_router(quotes.router, prefix="/quotes", tags=["Cotizaciones"])

# 3. Webhook de WhatsApp
api_router.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])

# 4. Endpoint de Conversaciones
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversaciones"])

# 5. Dashboard KPIs
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

# 6. Prompt training por cuenta
api_router.include_router(prompt_training.router, prefix="/prompt-training", tags=["Prompt Training"])
