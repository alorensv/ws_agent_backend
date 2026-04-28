import os
from datetime import datetime

from app.infrastructure.db.base import get_supabase

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

    def update_client_profile(self, client_id: str, data: dict):
        """Actualiza campos específicos del perfil del cliente (email, full_name)."""
        try:
            update_payload = {
                "last_interaction": datetime.utcnow().isoformat()
            }
            if data.get("full_name"): update_payload["full_name"] = data["full_name"]
            if data.get("email"): update_payload["email"] = data["email"]
            
            if len(update_payload) > 1:
                self.supabase.table("clients").update(update_payload).eq("id", client_id).execute()
        except Exception as e:
            print(f"ERROR REPO update_client_profile: {str(e)}")

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

    def update_quote(self, quote_id: str, payload: dict):
        """Actualiza campos de una cotizacion existente."""
        try:
            self.supabase.table("quotes")\
                .update(payload)\
                .eq("id", quote_id)\
                .execute()
        except Exception as e:
            print(f"ERROR REPO update_quote: {str(e)}")

    def _format_quote_dashboard_item(self, quote: dict):
        client = quote.get("clients") or {}
        item = quote.get("catalog_items") or {}
        amount = float(quote.get("calculated_price") or 0)
        phone = client.get("phone_number") or ""
        normalized_phone = "".join(ch for ch in phone if ch.isdigit())
        pdf_url = quote.get("pdf_url")

        return {
            "id": str(quote.get("id")),
            "account_id": str(quote.get("account_id")) if quote.get("account_id") else None,
            "client_id": str(quote.get("client_id")) if quote.get("client_id") else None,
            "item_id": str(quote.get("item_id")) if quote.get("item_id") else None,
            "client_name": client.get("full_name") or "Cliente sin nombre",
            "client_email": client.get("email") or "",
            "phone": phone or "N/A",
            "phone_digits": normalized_phone,
            "product": item.get("name", "Servicio sin definir"),
            "category": item.get("category") or "",
            "product_description": item.get("description") or "",
            "requirements": quote.get("user_requirements") or "",
            "amount": amount,
            "total": f"${amount:,.0f}" if amount else "$0",
            "status": quote.get("status", "pending"),
            "date": quote.get("created_at"),
            "created_at": quote.get("created_at"),
            "last_interaction": client.get("last_interaction"),
            "pdf_url": pdf_url,
            "has_pdf": bool(pdf_url),
            "chat_history": client.get("chat_history", []) or [],
            "whatsapp_url": f"https://wa.me/{normalized_phone}" if normalized_phone else None,
            "client_profile": {
                "full_name": client.get("full_name") or "",
                "email": client.get("email") or "",
                "phone_number": phone or "",
                "last_interaction": client.get("last_interaction"),
            },
        }

    def get_recent_quotes(self, limit: int = 10):
        """Retorna las cotizaciones mas recientes con detalles de cliente y catalogo."""
        try:
            res = self.supabase.table("quotes")\
                .select("id, account_id, client_id, item_id, user_requirements, calculated_price, pdf_url, status, created_at, clients(phone_number, full_name, email, chat_history, last_interaction), catalog_items(name, category, description)")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            return [self._format_quote_dashboard_item(q) for q in (res.data or [])]
        except Exception as e:
            print(f"ERROR REPO get_recent_quotes: {str(e)}")
            return []

    def get_recent_quotes_by_account(self, account_id: str, limit: int = 10):
        """Retorna las cotizaciones mas recientes filtradas por cuenta."""
        try:
            res = self.supabase.table("quotes")\
                .select("id, account_id, client_id, item_id, user_requirements, calculated_price, pdf_url, status, created_at, clients(phone_number, full_name, email, chat_history, last_interaction), catalog_items(name, category, description)")\
                .eq("account_id", account_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            return [self._format_quote_dashboard_item(q) for q in (res.data or [])]
        except Exception as e:
            print(f"ERROR REPO get_recent_quotes_by_account: {str(e)}")
            return []

    def list_quotes_by_account(self, account_id: str, limit: int = 100):
        """Retorna cotizaciones completas para el panel comercial."""
        try:
            res = self.supabase.table("quotes")\
                .select("id, account_id, client_id, item_id, user_requirements, calculated_price, pdf_url, status, created_at, clients(phone_number, full_name, email, chat_history, last_interaction), catalog_items(name, category, description)")\
                .eq("account_id", account_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            return [self._format_quote_dashboard_item(q) for q in (res.data or [])]
        except Exception as e:
            print(f"ERROR REPO list_quotes_by_account: {str(e)}")
            return []

    def get_quote_pdf_source(self, quote_id: str):
        """Obtiene la referencia del PDF asociado a una cotizacion."""
        try:
            res = self.supabase.table("quotes")\
                .select("id, pdf_url")\
                .eq("id", quote_id)\
                .limit(1)\
                .execute()

            if not res.data:
                return None

            row = res.data[0]
            pdf_url = row.get("pdf_url")
            if not pdf_url:
                return None

            is_remote = str(pdf_url).startswith("http://") or str(pdf_url).startswith("https://")
            return {
                "id": str(row.get("id")),
                "pdf_url": pdf_url,
                "is_remote": is_remote,
                "exists": True if is_remote else os.path.exists(pdf_url),
            }
        except Exception as e:
            print(f"ERROR REPO get_quote_pdf_source: {str(e)}")
            return None

    def get_all_conversations(self):
        """Retorna todos los clientes con su historial de chat, ordenados por ultima interaccion."""
        try:
            res = self.supabase.table("clients")\
                .select("id, phone_number, full_name, session_state, chat_history, last_interaction")\
                .order("last_interaction", desc=True)\
                .execute()
            return [
                {
                    "id": str(item.get("id")),
                    "phone_number": item.get("phone_number"),
                    "full_name": item.get("full_name"),
                    "session_state": item.get("session_state") or {},
                    "chat_history": item.get("chat_history") or [],
                    "last_interaction": item.get("last_interaction"),
                }
                for item in (res.data or [])
            ]
        except Exception as e:
            print(f"ERROR REPO get_all_conversations: {str(e)}")
            return []

    def get_conversations_by_account(self, account_id: str):
        """Retorna conversaciones filtradas por cuenta."""
        try:
            res = self.supabase.table("clients")\
                .select("id, phone_number, full_name, session_state, chat_history, last_interaction")\
                .eq("account_id", account_id)\
                .order("last_interaction", desc=True)\
                .execute()
            return [
                {
                    "id": str(item.get("id")),
                    "phone_number": item.get("phone_number"),
                    "full_name": item.get("full_name"),
                    "session_state": item.get("session_state") or {},
                    "chat_history": item.get("chat_history") or [],
                    "last_interaction": item.get("last_interaction"),
                }
                for item in (res.data or [])
            ]
        except Exception as e:
            print(f"ERROR REPO get_conversations_by_account: {str(e)}")
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

    def get_kpis_by_account(self, account_id: str):
        """Calcula KPIs filtrados por cuenta."""
        try:
            now_iso = datetime.utcnow().strftime("%Y-%m-%d")

            res_quotes = self.supabase.table("quotes")\
                .select("id", count="exact")\
                .eq("account_id", account_id)\
                .gte("created_at", now_iso)\
                .execute()
            cotizaciones_hoy = res_quotes.count if res_quotes.count is not None else len(res_quotes.data)

            res_leads = self.supabase.table("clients")\
                .select("id", count="exact")\
                .eq("account_id", account_id)\
                .gte("created_at", now_iso)\
                .execute()
            nuevos_leads = res_leads.count if res_leads.count is not None else len(res_leads.data)

            res_active = self.supabase.table("clients")\
                .select("id", count="exact")\
                .eq("account_id", account_id)\
                .gte("last_interaction", now_iso)\
                .execute()
            active_today = res_active.count if res_active.count is not None else len(res_active.data)

            conversion_pct = int((cotizaciones_hoy / max(active_today, 1)) * 100)
            if conversion_pct > 100:
                conversion_pct = 100

            return {
                "cotizaciones_hoy": str(cotizaciones_hoy),
                "nuevos_leads": str(nuevos_leads),
                "tiempo_respuesta": "1m 15s",
                "conversion": f"{conversion_pct}%"
            }
        except Exception as e:
            print(f"ERROR REPO get_kpis_by_account: {str(e)}")
            return {"cotizaciones_hoy": "0", "nuevos_leads": "0", "tiempo_respuesta": "0s", "conversion": "0%"}

    def get_active_accounts(self):
        """Retorna cuentas activas para poblar selectores del dashboard."""
        try:
            res = self.supabase.table("accounts")\
                .select("id, name, wsp_phone_id, system_prompt, active, created_at")\
                .eq("active", True)\
                .order("created_at", desc=False)\
                .execute()
            return [
                {
                    "id": str(account.get("id")),
                    "name": account.get("name"),
                    "wsp_phone_id": account.get("wsp_phone_id"),
                    "system_prompt": account.get("system_prompt") or "",
                    "active": account.get("active", True),
                    "created_at": account.get("created_at"),
                }
                for account in (res.data or [])
            ]
        except Exception as e:
            print(f"ERROR REPO get_active_accounts: {str(e)}")
            return []

    def get_account_prompt(self, account_id: str):
        """Obtiene el system prompt de una cuenta."""
        try:
            res = self.supabase.table("accounts")\
                .select("id, name, system_prompt, created_at")\
                .eq("id", account_id)\
                .limit(1)\
                .execute()

            if not res.data:
                return None

            account = res.data[0]
            return {
                "account_id": str(account["id"]),
                "account_name": account.get("name") or "Cuenta",
                "system_prompt": account.get("system_prompt") or "",
                "updated_at": account.get("created_at")
            }
        except Exception as e:
            print(f"ERROR REPO get_account_prompt: {str(e)}")
            return None

    def update_account_prompt(self, account_id: str, system_prompt: str):
        """Actualiza el system prompt de una cuenta y devuelve el registro actualizado."""
        try:
            self.supabase.table("accounts")\
                .update({"system_prompt": system_prompt})\
                .eq("id", account_id)\
                .execute()

            return self.get_account_prompt(account_id)
        except Exception as e:
            print(f"ERROR REPO update_account_prompt: {str(e)}")
            return None

    def list_catalog_items(self, account_id: str, include_inactive: bool = False):
        """Lista items del catalogo por cuenta."""
        try:
            query = self.supabase.table("catalog_items")\
                .select("id, account_id, category, name, description, base_price, specifications, is_active, created_at")\
                .eq("account_id", account_id)\
                .order("created_at", desc=False)

            if not include_inactive:
                query = query.eq("is_active", True)

            res = query.execute()
            return [
                {
                    "id": str(item.get("id")),
                    "account_id": str(item.get("account_id")),
                    "category": item.get("category") or "",
                    "name": item.get("name") or "",
                    "description": item.get("description") or "",
                    "base_price": float(item.get("base_price") or 0),
                    "specifications": item.get("specifications") or {},
                    "is_active": item.get("is_active", True),
                    "created_at": item.get("created_at"),
                }
                for item in (res.data or [])
            ]
        except Exception as e:
            print(f"ERROR REPO list_catalog_items: {str(e)}")
            return []

    def get_catalog_item(self, account_id: str, item_id: str):
        """Obtiene un item del catalogo por cuenta."""
        try:
            res = self.supabase.table("catalog_items")\
                .select("id, account_id, category, name, description, base_price, specifications, is_active, created_at")\
                .eq("account_id", account_id)\
                .eq("id", item_id)\
                .limit(1)\
                .execute()

            if not res.data:
                return None

            item = res.data[0]
            return {
                "id": str(item.get("id")),
                "account_id": str(item.get("account_id")),
                "category": item.get("category") or "",
                "name": item.get("name") or "",
                "description": item.get("description") or "",
                "base_price": float(item.get("base_price") or 0),
                "specifications": item.get("specifications") or {},
                "is_active": item.get("is_active", True),
                "created_at": item.get("created_at"),
            }
        except Exception as e:
            print(f"ERROR REPO get_catalog_item: {str(e)}")
            return None

    def create_catalog_item(self, payload: dict):
        """Crea un item del catalogo."""
        try:
            res = self.supabase.table("catalog_items").insert(payload).execute()
            if not res.data:
                return None
            created = res.data[0]
            return self.get_catalog_item(str(created.get("account_id")), str(created.get("id")))
        except Exception as e:
            print(f"ERROR REPO create_catalog_item: {str(e)}")
            return None

    def update_catalog_item(self, account_id: str, item_id: str, payload: dict):
        """Actualiza un item del catalogo."""
        try:
            self.supabase.table("catalog_items")\
                .update(payload)\
                .eq("account_id", account_id)\
                .eq("id", item_id)\
                .execute()
            return self.get_catalog_item(account_id, item_id)
        except Exception as e:
            print(f"ERROR REPO update_catalog_item: {str(e)}")
            return None
