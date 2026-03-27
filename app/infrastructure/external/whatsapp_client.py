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
        
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                res = await client.post(
                    url,
                    headers=headers,
                    files={"file": (file_path, f, "application/pdf")},
                    data={"messaging_product": "whatsapp"}
                )
                print(f"RES WSP UPLOAD: {res.status_code}")
                return res.json().get("id")

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
            print(f"RES WSP SEND DOC: {res.status_code}")
            return res.json()
