import httpx
from app.core.config import settings

class WhatsAppClient:
    def __init__(self):
        # Valores base por defecto (Globales)
        self.base_url = "https://graph.facebook.com/v19.0"
        self.global_phone_id = settings.wsp_phone_id
        self.global_token = settings.wsp_token

    def _get_headers(self, token: str = None):
        return {"Authorization": f"Bearer {token if token else self.global_token}"}

    def _get_url(self, phone_id: str = None):
        return f"{self.base_url}/{phone_id if phone_id else self.global_phone_id}"

    async def send_text(self, phone: str, text: str, phone_id: str = None, token: str = None):
        """Envía un mensaje de texto simple a través de una cuenta específica."""
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": text}
        }
        url = f"{self._get_url(phone_id)}/messages"
        headers = self._get_headers(token)
        
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, headers=headers)
            print(f"RES WSP SEND: {res.status_code}")
            return res.json()

    async def upload_media(self, file_path: str, phone_id: str = None, token: str = None):
        """Sube un archivo a Meta para una cuenta específica."""
        url = f"{self._get_url(phone_id)}/media"
        headers = self._get_headers(token)
        
        import os
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                res = await client.post(
                    url,
                    headers=headers,
                    files={"file": (os.path.basename(file_path), f, "application/pdf")},
                    data={"messaging_product": "whatsapp"}
                )
                if res.status_code != 200:
                    print(f"ERROR WSP UPLOAD: {res.status_code} - {res.text}")
                    return None
                
                media_id = res.json().get("id")
                print(f"SUCCESS WSP UPLOAD: {media_id}")
                return media_id

    async def send_document(self, phone: str, media_id: str, filename: str, phone_id: str = None, token: str = None):
        """Envía un documento PDF a través de una cuenta específica."""
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "document",
            "document": {"id": media_id, "filename": filename}
        }
        url = f"{self._get_url(phone_id)}/messages"
        headers = self._get_headers(token)

        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, headers=headers)
            if res.status_code != 200:
                print(f"ERROR WSP SEND DOC: {res.status_code} - {res.text}")
            else:
                print(f"SUCCESS WSP SEND DOC: {res.status_code}")
            return res.json()

    async def send_buttons(self, phone: str, text: str, buttons: list, phone_id: str = None, token: str = None):
        """Envía un mensaje con botones interactivos (máximo 3)."""
        # Formatear botones para la API de WhatsApp
        formatted_buttons = []
        for i, btn_title in enumerate(buttons[:3]): # WhatsApp permite máximo 3 botones de respuesta rápida
            formatted_buttons.append({
                "type": "reply",
                "reply": {
                    "id": f"btn_{i}",
                    "title": btn_title[:20] # El título tiene un límite de 20 caracteres
                }
            })

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": text},
                "action": {"buttons": formatted_buttons}
            }
        }
        url = f"{self._get_url(phone_id)}/messages"
        headers = self._get_headers(token)

        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, headers=headers)
            print(f"RES WSP SEND BUTTONS: {res.status_code}")
            return res.json()
