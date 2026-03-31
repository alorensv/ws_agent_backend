from fastapi import APIRouter, Request, HTTPException, Query, Response
from app.core.config import settings
from app.domain.services.conversation_service import ConversationService

router = APIRouter()

@router.get("/info")
async def get_webhook_info(request: Request):
    """Genera dinámicamente la URL completa del Webhook basada en el dominio del entorno (Vercel)."""
    base_url = str(request.base_url).rstrip('/')
    return {
        "webhook_url": f"{base_url}/api/v1/webhook/whatsapp",
        "verify_token": settings.wsp_verify_token,
        "instructions": "Usa estos datos en el Meta Developer Portal para configurar el webhook."
    }

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
        # Meta espera el challenge EXACTAMENTE como texto plano, sin comillas (No JSON).
        return Response(content=str(challenge), media_type="text/plain")
    
    # Si llega sin parámetros o con token incorrecto, lanzamos 403
    print(f"WEBHOOK ERROR: Mode={mode}, TokenReceived={token}, TokenExpected={settings.wsp_verify_token}")
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
