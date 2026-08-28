import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from sqlalchemy import create_engine, text
import jwt
def print_step(title: str):
    print(f"\n[{title}]")
def print_ok(msg: str):
    print(f"  [OK] {msg}")
def print_warn(msg: str):
    print(f"  [WARN] {msg}")
def print_fail(msg: str):
    print(f"  [FAIL] {msg}")
def test_postgres_connection() -> bool:
    print_step("1. PostgreSQL Connection")
    db_uri = settings.SQLALCHEMY_DATABASE_URI
    masked_uri = db_uri
    if "@" in masked_uri and ":" in masked_uri.split("@")[0]:
        user_part, host_part = masked_uri.split("@", 1)
        prefix, _ = user_part.rsplit(":", 1)
        masked_uri = f"{prefix}:****@{host_part}"
    print(f"  Target URI: {masked_uri}")
    try:
        engine = create_engine(db_uri, pool_pre_ping=True)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            db_version = result.scalar()
            print_ok("Database connection established")
            print(f"  Version: {db_version[:60]}...")
            table_check = connection.execute(
                text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users');")
            )
            exists = table_check.scalar()
            if exists:
                user_count = connection.execute(text("SELECT COUNT(*) FROM users;")).scalar()
                print_ok(f"Table 'users' exists ({user_count} records)")
            else:
                print_warn("Table 'users' not created yet")
        return True
    except Exception as e:
        print_fail(f"PostgreSQL connection failed: {e}")
        return False
def test_supabase_api() -> bool:
    print_step("2. Supabase API Client")
    if not settings.SUPABASE_URL:
        print_warn("SUPABASE_URL not configured")
        return True
    api_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    if not api_key:
        print_warn("No Supabase key configured")
        return True
    try:
        from supabase import create_client
        create_client(settings.SUPABASE_URL, api_key)
        print_ok(f"Supabase client initialized for {settings.SUPABASE_URL}")
        return True
    except Exception as e:
        print_fail(f"Supabase client error: {e}")
        return False
def test_jwt_secret() -> bool:
    print_step("3. Supabase JWT Validation")
    secret = settings.SUPABASE_JWT_SECRET
    if not secret:
        print_warn("SUPABASE_JWT_SECRET not configured")
        return False
    try:
        payload = {
            "sub": "test-user-id",
            "email": "test@sagar.org",
            "aud": "authenticated",
            "role": "authenticated",
            "exp": int(time.time()) + 300,
            "iat": int(time.time()),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
        assert decoded["sub"] == "test-user-id"
        print_ok("JWT sign and verify passed")
        return True
    except Exception as e:
        print_fail(f"JWT verification failed: {e}")
        return False
def main():
    print("=" * 60)
    print(f"SAGAR Connection Check | Environment: {settings.ENVIRONMENT}")
    print("=" * 60)
    pg_ok = test_postgres_connection()
    api_ok = test_supabase_api()
    jwt_ok = test_jwt_secret()
    print("\n" + "=" * 60)
    if pg_ok and api_ok and jwt_ok:
        print("RESULT: All checks passed")
    else:
        print("RESULT: One or more checks failed")
    print("=" * 60)
if __name__ == "__main__":
    main()