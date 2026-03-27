from supabase import create_client, Client
from app.core.config import settings

def get_supabase() -> Client:
    """Retorna clientes singleton de Supabase."""
    try:
        url = settings.supabase_url
        key = settings.supabase_key
        return create_client(url, key)
    except Exception as e:
        print(f"ERROR CONNECTING TO SUPABASE: {str(e)}")
        raise e
