import os
import httpx
from app.core.config import settings

class AIClient:
    def __init__(self):
        # Usamos DeepSeek API para conversaciones naturales de Alejandro Lorens
        self.api_key = settings.openai_api_key
        self.api_base = settings.deepseek_api_base
        
        self.v3_system_prompt = """
        Eres un Consultor de Ventas Multidisciplinario Experto (Versión Lineas de Código - Alejandro Lorens).
        Tu misión es recomendar estructuras web proactivamente y guiar al usuario.

        CATÁLOGO REAL:
        {context}

        INSTRUCCIONES CLAVE:
        1. Identificación: Si busca algo "simple", sugiere una LANDING PAGE (Banner, Servicios, Casos de Éxito, Formulario).
        2. Cualificación: Antes de cotizar, pregunta por Logo, Colores y Objetivo del sitio.
        3. Recotización: Ajusta el 'base_price' si el usuario da detalles específicos.
        4. Acción Técnica: Si el usuario desea la cotización formal, incluye al final de tu respuesta: TRIGGER_GENERATE_QUOTE.
        5. REGLA ESTRICTA: BAJO NINGUNA CIRCUNSTANCIA sugieras productos, servicios, plataformas externas (como Wix, WordPress, Shopify), freelancers o agencias de terceros. Si el usuario rechaza tu propuesta o no desea continuar, despídete cordialmente y ofrécele comunicarse con un ejecutivo humano de nuestro equipo.

        TONO: Ejecutivo y profesional. Moneda: CLP.
        Inicia presentándote como el bot de Alejandro, tu consultor digital.
        """

    async def get_response(self, chat_history: list, user_message: str, catalog_context: str, current_state: dict, custom_prompt: str = None):
        """Llamada asíncrona a la API de DeepSeek para obtener respuesta conversacional."""
        # Usar el prompt de la cuenta o el por defecto de Alejandro Lorens
        base_prompt = custom_prompt if custom_prompt else self.v3_system_prompt
        system_message = base_prompt.replace("{context}", catalog_context)
        
        messages = [{"role": "system", "content": system_message}]
        
        # Inyectar historial relevante (máx 5 mensajes previos)
        actual_history = chat_history if isinstance(chat_history, list) else []
        for h in actual_history[-5:]:
            role = "assistant" if h.get("sender") == "bot" else "user"
            messages.append({"role": role, "content": h.get("message", "")})
            
        messages.append({"role": "user", "content": user_message})

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                if res.status_code != 200:
                    return {"text": "Lo siento, tuve un problema al procesar tu respuesta.", "intent": "error"}
                    
                data = res.json()
                ai_text = data["choices"][0]["message"]["content"]
                
                # Análisis de intención básico
                intent = "chat"
                if "TRIGGER_GENERATE_QUOTE" in ai_text:
                    intent = "generate_quote_v2"
                    ai_text = ai_text.replace("TRIGGER_GENERATE_QUOTE", "").strip()

                return {
                    "text": ai_text,
                    "intent": intent,
                    "next_state": {"last_intent": intent}
                }
        except Exception as e:
            print(f"Error AI Client: {str(e)}")
            return {"text": "Error técnico con la IA.", "intent": "error"}
