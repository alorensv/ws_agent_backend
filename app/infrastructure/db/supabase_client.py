from supabase import create_client, Client
from app.core.config import settings

def get_supabase() -> Client:
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError("Supabase credentials not found in settings")
    return create_client(settings.supabase_url, settings.supabase_key)
