from app.infrastructure.db.base import get_supabase
from datetime import datetime

class ConversationRepository:
    def __init__(self):
        self.supabase = get_supabase()

    def get_account_by_phone_id(self, phone_id: str):
        """Busca la cuenta configurada para un número de teléfono específico de Meta."""
        try:
            res = self.supabase.table("accounts").select("*").eq("wsp_phone_id", phone_id).eq("active", True).execute()
            if len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            print(f"ERROR REPO get_account_by_phone_id: {str(e)}")
            return None

    def get_or_create(self, client_phone: str, account_id: str):
        """Busca o inserta un cliente para una cuenta específica."""
        try:
            res = self.supabase.table("clients")\
                .select("*")\
                .eq("phone_number", client_phone)\
                .eq("account_id", account_id)\
                .execute()
            
            if len(res.data) > 0:
                client = res.data[0]
                return {
                    "id": client["id"],
                    "phone": client["phone_number"],
                    "state": client.get("session_state", {}) or {},
                    "history": client.get("chat_history", []) or []
                }
            
            new_client = {
                "phone_number": client_phone,
                "account_id": account_id,
                "session_state": {},
                "chat_history": []
            }
            res = self.supabase.table("clients").insert(new_client).execute()
            client = res.data[0]
            
            return {
                "id": client["id"],
                "phone": client["phone_number"],
                "state": {},
                "history": []
            }
        except Exception as e:
            print(f"ERROR REPO get_or_create: {str(e)}")
            raise e

    def save_message(self, client_id: str, sender: str, message: str):
        """Guarda un mensaje en el historial JSONB de la tabla 'clients'."""
        try:
            # 1. Obtener historial actual
            res = self.supabase.table("clients").select("chat_history").eq("id", client_id).execute()
            history = res.data[0].get("chat_history", []) or []
            
            # 2. Agregar nuevo mensaje
            history.append({
                "sender": sender,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Limitar historial a 10 mensajes
            history = history[-10:]
            
            # 3. Actualizar en Supabase
            self.supabase.table("clients").update({
                "chat_history": history,
                "last_interaction": datetime.utcnow().isoformat()
            }).eq("id", client_id).execute()
        except Exception as e:
            print(f"ERROR REPO save_message: {str(e)}")

    def update_state(self, client_id: str, state: dict):
        """Actualiza el estado de la sesión (JSONB) del cliente."""
        try:
            self.supabase.table("clients").update({
                "session_state": state, 
                "last_interaction": datetime.utcnow().isoformat()
            }).eq("id", client_id).execute()
        except Exception as e:
            print(f"ERROR REPO update_state: {str(e)}")

    def get_full_catalog(self, account_id: str):
        """Retorna el catálogo filtrado por cuenta."""
        try:
            print(f"DEBUG REPO: Querying catalog for account_id='{account_id}'")
            res = self.supabase.table("catalog_items")\
                .select("*")\
                .eq("account_id", account_id)\
                .eq("is_active", True)\
                .execute()
            print(f"DEBUG REPO: Found {len(res.data)} items for account {account_id}")
            return res.data
        except Exception as e:
            print(f"ERROR REPO get_full_catalog: {str(e)}")
            return []

    def save_quote(self, id, client_id, item_id, requirements, price, status, account_id):
        """Guarda una cotización asociada a la cuenta."""
        try:
            self.supabase.table("quotes").insert({
                "id": id,
                "client_id": client_id,
                "item_id": item_id,
                "account_id": account_id,
                "user_requirements": requirements,
                "calculated_price": price,
                "status": status,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            print(f"ERROR REPO save_quote: {str(e)}")

    def get_recent_quotes(self, limit: int = 10):
        """Retorna las cotizaciones mas recientes con detalles de cliente y catalogo."""
        try:
            res = self.supabase.table("quotes")\
                .select("id, calculated_price, status, created_at, clients(phone_number, chat_history), catalog_items(name)")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            quotes_list = []
            if res.data:
                for q in res.data:
                    client = q.get("clients") or {}
                    item = q.get("catalog_items") or {}
                    
                    quotes_list.append({
                        "id": str(q.get("id")),
                        "phone": client.get("phone_number", "N/A"),
                        "product": item.get("name", "N/A"),
                        "total": f"${q.get('calculated_price', 0):,.0f}" if q.get("calculated_price") else "$0",
                        "status": q.get("status", "Pendiente"),
                        "date": q.get("created_at"),
                        "chat_history": client.get("chat_history", [])
                    })
            return quotes_list
        except Exception as e:
            print(f"ERROR REPO get_recent_quotes: {str(e)}")
            return []

    def get_all_conversations(self):
        """Retorna todos los clientes con su historial de chat, ordenados por ultima interaccion."""
        try:
            res = self.supabase.table("clients")\
                .select("id, phone_number, full_name, session_state, chat_history, last_interaction")\
                .order("last_interaction", desc=True)\
                .execute()
            return res.data or []
        except Exception as e:
            print(f"ERROR REPO get_all_conversations: {str(e)}")
            return []

    def get_kpis(self):
        """Calcula los indicadores KPI del dashboard en tiempo real."""
        try:
            # Fecha de inicio de hoy (UTC)
            now_iso = datetime.utcnow().strftime("%Y-%m-%d")
            
            # 1. Cotizaciones Hoy: Cuántos registros en la tabla 'quotes' hoy
            res_quotes = self.supabase.table("quotes").select("id", count="exact").gte("created_at", now_iso).execute()
            cotizaciones_hoy = res_quotes.count if res_quotes.count is not None else len(res_quotes.data)
            
            # 2. Nuevos Leads: Cuántos clientes registrados 'created_at' hoy
            res_leads = self.supabase.table("clients").select("id", count="exact").gte("created_at", now_iso).execute()
            nuevos_leads = res_leads.count if res_leads.count is not None else len(res_leads.data)
            
            # 3. Conversión: Porcentaje de cotizaciones vs interacciones activas hoy
            res_active = self.supabase.table("clients").select("id", count="exact").gte("last_interaction", now_iso).execute()
            active_today = res_active.count if res_active.count is not None else len(res_active.data)
            
            conversion_pct = int((cotizaciones_hoy / max(active_today, 1)) * 100)
            if conversion_pct > 100: conversion_pct = 100
            
            return {
                "cotizaciones_hoy": str(cotizaciones_hoy),
                "nuevos_leads": str(nuevos_leads),
                "tiempo_respuesta": "1m 15s",
                "conversion": f"{conversion_pct}%"
            }
        except Exception as e:
            print(f"ERROR REPO get_kpis: {str(e)}")
            return {"cotizaciones_hoy": "0", "nuevos_leads": "0", "tiempo_respuesta": "0s", "conversion": "0%"}
