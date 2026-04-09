import uuid
from app.infrastructure.db.repositories.conversation_repository import ConversationRepository
from app.infrastructure.external.whatsapp_client import WhatsAppClient
from app.utils.helpers import PdfHelper

class QuoteService:
    def __init__(self):
        self.repo = ConversationRepository()
        self.wsp = WhatsAppClient()
        self.pdf_helper = PdfHelper()

    async def process_v2_quote(self, client: dict, item: dict, user_text: str, account: dict):
        """Generar presupuesto dinámico asociado a la cuenta, guardarlo y enviarlo al usuario."""
        quote_id = str(uuid.uuid4())
        account_id = account["id"]
        base_price = float(item.get("base_price", 500000))
        
        # Simulación de ajuste de precio basado en detalles (30% incremento si hay specs)
        final_price = base_price
        if any(w in user_text.lower() for w in ["detalles", "especifico", "personalizado", "mas", "info"]):
            final_price = base_price * 1.3
            
        items_payload = [{"name": item["name"].upper(), "qty": 1, "price": final_price}]
        
        # 1. Persistencia: Guardar en Supabase (quotes_v2) con account_id
        print(f"DEBUG STEP 1 - Guardando cotización en Supabase para {client['phone']}")
        self.repo.save_quote(
            id=quote_id,
            client_id=client["id"],
            item_id=item["id"],
            requirements=user_text,
            price=final_price,
            status="pending_validation",
            account_id=account_id
        )
        
        # 2. Generación de PDF: PDFHelper se encarga de ReportLab
        print(f"DEBUG STEP 2 - Generando PDF físico")
        quote_data = {"id": quote_id, "items": items_payload, "total": final_price}
        client_info = {"phone": client["phone"], "name": "Potencial Cliente (V2.5)"}
        pdf_path = self.pdf_helper.generate_quote_pdf(quote_data, client_info)
        
        # 3. Envío: Subir a Meta y mandar al chat usando credenciales de la cuenta
        print(f"DEBUG STEP 3 - Subiendo y enviando vía WhatsApp para cuenta {account['name']}")
        wsp_phone_id = account.get("wsp_phone_id")
        wsp_token = account.get("wsp_token")

        media_id = await self.wsp.upload_media(pdf_path, phone_id=wsp_phone_id, token=wsp_token)
        
        if media_id:
            pdf_name = f"Cotizacion_{str(quote_id)[:4]}.pdf"
            await self.wsp.send_document(client["phone"], media_id, pdf_name, phone_id=wsp_phone_id, token=wsp_token)
            
            # Mensaje de Cierre y Validación
            msg = f"✅ **Propuesta Formal Generada por ${final_price:,.0f} CLP**\n\n⚠️ **Importante**: Este es un valor de referencia. Un ejecutivo comercial validará tu requerimiento en breve para darte el sello final de aprobación."
            await self.wsp.send_text(client["phone"], msg, phone_id=wsp_phone_id, token=wsp_token)
            
            # Actualizar historial
            self.repo.save_message(client["id"], "bot", f"Cotización enviada: {quote_id}")
            return {"status": "quote_v2_sent", "quote_id": quote_id}
        else:
            print(f"ERROR: No se pudo obtener media_id para el PDF.")
            error_msg = "Lo siento, tuve un problema al generar tu archivo PDF. Pero no te preocupes, un ejecutivo se contactará contigo para enviártelo manualmente."
            await self.wsp.send_text(client["phone"], error_msg, phone_id=wsp_phone_id, token=wsp_token)
            return {"status": "error_sending_pdf"}
