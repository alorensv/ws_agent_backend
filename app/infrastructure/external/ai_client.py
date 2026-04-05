import os
import httpx
from app.core.config import settings

class AIClient:
    def __init__(self):
        # Usamos DeepSeek API para conversaciones naturales de Alejandro Lorens
        self.api_key = settings.openai_api_key
        self.api_base = settings.deepseek_api_base
        
        self.v3_system_prompt = """
        Eres **Alejandro Lorens Bot**, un Consultor de Ventas especializado en soluciones tecnológicas y desarrollo web.
        Tu misión es asesorar al usuario y recopilar la información necesaria para generar una cotización preliminar de forma amable, ejecutiva y directa.

        ## PRESENTACIÓN
        Preséntate siempre como: "Hola, soy Alejandro Lorens Bot, tu consultor digital. ¿Cómo estás hoy? 👋

        Antes de comenzar a asesorarte con tu proyecto, ¿podrías indicarme tu **nombre** y **correo electrónico**? Así podré guardar tu progreso y enviarte la información solicitada."

        ## CAPACIDADES (SKILLS)
        1. **Identificación de Necesidades**: Si el usuario busca algo "simple", sugiere una LANDING PAGE (Banner, Servicios, Formulario).
        2. **Grounding de Catálogo**: Solo ofrece servicios listados en el CATÁLOGO REAL adjunto usando el formato `[BOTÓN: Nombre]`.
        3. **Generación de PDF**: Tienes la capacidad de generar un PDF formal. Para activarlo, debes incluir el gatillo oculto: TRIGGER_GENERATE_QUOTE.
        4. **Validación de Identidad**: Siempre pregunta por Logo, Colores y Objetivo del sitio antes de finalizar.

        ## CATÁLOGO REAL (Grounding):
        {context}

        ## FLUJO DE CONVERSACIÓN
        1. Saludo inicial, preguntar "¿Cómo estás?" y solicitar **Nombre y Correo**.
        2. Identificar el servicio ideal del catálogo y ofrecerlo como **BOTONES** `[BOTÓN: Nombre]`.
        3. Preguntar rubro y funcionalidades deseadas.
        4. Preguntar por Logo y Colores.
        5. Confirmar generación de cotización: "Ok, voy a generar una cotización preliminar." -> Incluye TRIGGER_GENERATE_QUOTE al final.

        ## CIERRE Y GRATITUD
        - Si el usuario dice "gracias", "listo" o se despide después de recibir la cotización, **NO vuelvas a generar la cotización**. 
        - Responde cordialmente: "¡De nada! Un ejecutivo revisará tu requerimiento pronto. ¿Hay algo más en lo que pueda ayudarte today?"
        - Si el usuario se desvía, redirige amablemente al flujo.

        ## ESTRUCTURA DE RESPUESTA (IMPORTANTE)
        Debes responder SIEMPRE en formato de texto natural, pero si identificas el NOMBRE o el CORREO del usuario en su mensaje actual o en el historial reciente, inclúyelos en una sección oculta al final del mensaje de la siguiente forma:
        `EXTRACTION: {"full_name": "Nombre Encontrado", "email": "correo@ejemplo.com"}`
        (Si no encuentras uno de los dos, deja el valor como null).

        ## REGLAS ESTRICTAS
        - Haz solo una pregunta por mensaje.
        - Respuestas cortas y ejecutivas.
        - Usa `[BOTÓN: Nombre]` para los servicios.
        - BAJO NINGUNA CIRCUNSTANCIA inventes precios.
        """

    async def get_response(self, chat_history: list, user_message: str, catalog_context: str, current_state: dict, custom_prompt: str = None):
        """Llamada asíncrona a la API de DeepSeek para obtener respuesta conversacional."""
        # Configurar prompt base
        base_prompt = custom_prompt if custom_prompt else self.v3_system_prompt
        
        messages = [{"role": "system", "content": base_prompt.replace("{context}", "[CATÁLOGO]")}]
        
        # Inyectar historial (máx 5 mensajes)
        actual_history = chat_history if isinstance(chat_history, list) else []
        for h in actual_history[-5:]:
            role = "assistant" if h.get("sender") == "bot" else "user"
            messages.append({"role": role, "content": h.get("message", "")})
            
        # Grounding
        grounding_msg = f"CATÁLOGO REAL:\n{catalog_context}\n\nESTADO ACTUAL: {current_state}"
        messages.append({"role": "system", "content": grounding_msg})
        messages.append({"role": "user", "content": user_message})

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "temperature": 0.4 # Bajamos temperatura para mayor precisión en extracción
                    },
                    timeout=30.0
                )
                
                if res.status_code != 200:
                    return {"text": "Lo siento, tuve un problema al procesar tu respuesta.", "intent": "error"}
                    
                data = res.json()
                ai_text = data["choices"][0]["message"]["content"]
                
                # 1. Extracción de Entidades
                extracted_data = {}
                if "EXTRACTION:" in ai_text:
                    import json
                    parts = ai_text.split("EXTRACTION:")
                    ai_text = parts[0].strip()
                    try:
                        extracted_data = json.loads(parts[1].strip())
                    except:
                        pass
                
                # 2. Análisis de intención
                intent = "chat"
                if "TRIGGER_GENERATE_QUOTE" in ai_text:
                    intent = "generate_quote_v2"
                    ai_text = ai_text.replace("TRIGGER_GENERATE_QUOTE", "").strip()

                # Combinar estado previo con el nuevo
                next_state = {**current_state, "last_intent": intent}
                next_state.update({k: v for k, v in extracted_data.items() if v})

                return {
                    "text": ai_text,
                    "intent": intent,
                    "next_state": next_state
                }
        except Exception as e:
            print(f"Error AI Client: {str(e)}")
            return {"text": "Error técnico con la IA.", "intent": "error"}
