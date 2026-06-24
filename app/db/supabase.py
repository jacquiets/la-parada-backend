from supabase import create_client, Client
from app.core.config import settings

# Cliente con service role key — solo para uso interno del backend
# Bypasa Row Level Security y tiene permisos de admin
_supabase_admin: Client | None = None

# Cliente con anon key — para operaciones que respetan RLS
_supabase_client: Client | None = None


def get_supabase_admin() -> Client:
    """Retorna el cliente de Supabase con la service role key."""
    global _supabase_admin
    if _supabase_admin is None:
        _supabase_admin = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY,
        )
    return _supabase_admin


def get_supabase() -> Client:
    """Retorna el cliente de Supabase con la anon key."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY,
        )
    return _supabase_client
