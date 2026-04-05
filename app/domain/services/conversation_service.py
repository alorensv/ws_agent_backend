import uuid
from app.infrastructure.db.repositories.conversation_repository import ConversationRepository
from app.infrastructure.external.whatsapp_client import WhatsAppClient
from app.infrastructure.external.ai_client import AIClient
from app.domain.services.quote_service import QuoteService

class ConversationService:
    def __init__(self):
        self.repo = ConversationRepository()
        self.wsp = WhatsAppClient()
        self.ai = AIClient()
        self.quote_service = QuoteService()

    async def handle_message(self, payload: dict):
        try:
            # 1. Parsing del mensaje entrante y metadatos del receptor
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            # Identificar a qué número de Meta llegó el mensaje (Recipient)
            metadata = value.get("metadata", {})
            phone_id = metadata.get("phone_number_id")
            
            if not value.get("messages"):
                return {"status": "no_messages"}
                
            message = value.get("messages", [{}])[0]
            client_phone = message.get("from")
            user_text = message.get("text", {}).get("body", "")
            
            # 2. Identificación del Tenant (Cuenta)
            account = self.repo.get_account_by_phone_id(phone_id)
            if not account:
                print(f"CRITICAL: No account found for phone_id {phone_id}")
                return {"status": "account_not_found"}
                
            account_id = account["id"]
            system_prompt = account.get("system_prompt")

            # 3. Persistencia: Obtener Cliente e Historial filtrado por cuenta
            client = self.repo.get_or_create(client_phone, account_id)
            self.repo.save_message(client["id"], "user", user_text)
            
            # 4. Datos del Negocio (Grounding): Cargar Catálogo filtrado por cuenta
            catalog = self.repo.get_full_catalog(account_id)
            catalog_txt = "\n".join([f"- {i['name']} ({i['category']}): {i['description']} - ${i['base_price']}" for i in catalog])

            # 5. Inteligencia Artificial con prompt personalizado
            print(f"DEBUG - Consultando IA para cuenta {account['name']} ({client_phone})")
            ai_res = await self.ai.get_response(client["history"], user_text, catalog_txt, client["state"], custom_prompt=system_prompt)
            bot_text = ai_res.get("text", "")
            intent = ai_res.get("intent", "chat")

            # 6. Lógica de Negocio (Cotización con cuenta completa)
            if intent == "generate_quote_v2":
                print(f"DEBUG - Disparando Generación de Cotización para {account['name']}")
                if bot_text:
                    await self.wsp.send_text(
                        client_phone, 
                        bot_text, 
                        phone_id=account.get("wsp_phone_id"), 
                        token=account.get("wsp_token")
                    )
                item = self._match_catalog_item(user_text, catalog)
                return await self.quote_service.process_v2_quote(client, item, user_text, account)

            # 7. Responder al usuario vía WhatsApp usando credenciales de la cuenta
            await self.wsp.send_text(
                client_phone, 
                bot_text, 
                phone_id=account.get("wsp_phone_id"), 
                token=account.get("wsp_token")
            )
            
            # 8. Actualizar historial, estado y perfil en Supabase
            self.repo.save_message(client["id"], "bot", bot_text)
            next_state = ai_res.get("next_state", {})
            self.repo.update_state(client["id"], next_state)
            
            # Sincronizar campos de lead si fueron detectados
            if next_state.get("full_name") or next_state.get("email"):
                self.repo.update_client_profile(client["id"], next_state)
            
            return {"status": "message_sent", "account": account["name"]}

        except Exception as e:
            print(f"CRITICAL ERROR IN CONVERSATION SERVICE: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _match_catalog_item(self, text, catalog):
        """Lógica simple de matching basada en palabras clave del catálogo."""
        text = text.lower()
        for item in catalog:
            if item["name"].lower() in text or item["category"].lower() in text:
                return item
        return catalog[0] if catalog else None
