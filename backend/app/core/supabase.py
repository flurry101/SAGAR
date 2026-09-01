from typing import Optional
from supabase import create_client, Client
from app.config import settings

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Returns a configured Supabase client instance using service role key or anon key,
    or None if Supabase URL / key are not configured.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if settings.SUPABASE_URL and (settings.service_role_key or settings.SUPABASE_ANON_KEY):
        key = settings.service_role_key or settings.SUPABASE_ANON_KEY
        _supabase_client = create_client(settings.SUPABASE_URL, key)
        return _supabase_client

    if settings.SUPABASE_DB_URL and (settings.service_role_key or settings.SUPABASE_ANON_KEY):
        key = settings.service_role_key or settings.SUPABASE_ANON_KEY
        _supabase_client = create_client(settings.SUPABASE_URL or settings.SUPABASE_DB_URL.replace("postgresql", "postgres"), key)
        return _supabase_client

    return None
