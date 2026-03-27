from fastapi import APIRouter, Request, HTTPException, Query
from app.core.config import settings
from app.domain.services.conversation_service import ConversationService

router = APIRouter()

@router.get("/")
@router.get("/whatsapp")
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    """Verificación del webhook con Meta para activar WhatsApp Cloud API."""
    if mode == "subscribe" and token == settings.wsp_verify_token:
        print("WEBHOOK VERIFIED ✅")
        # Challenge puede ser string o int, Meta lo espera como el mismo valor recibido
        return challenge if challenge.isdigit() else challenge
    raise HTTPException(status_code=403, detail="Invalid token")

@router.post("/")
@router.post("/whatsapp")
async def receive_whatsapp(request: Request):
    """Recibir mensajes desde WhatsApp Cloud API y delegar al ConversationService."""
    try:
        payload = await request.json()
        print(f"WEBHOOK RECEIVED: {payload}")
        
        # Validar si hay cambios y mensajes
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        
        if "messages" not in value:
            print("Event ignored: No messages in payload")
            return {"status": "event_ignored"}

        # Delegar procesamiento al Servicio de Dominio (Asincrónico)
        service = ConversationService()
        await service.handle_message(payload)
        
        return {"status": "ok"}
    except Exception as e:
        print(f"ERROR WEBHOOK: {str(e)}")
        return {"status": "error_handled", "detail": str(e)}
