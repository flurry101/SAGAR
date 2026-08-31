"""
Database Migration Runner for SAGAR / ORCA.

Reads and applies SQL migration files against the target PostgreSQL / Supabase database.
"""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from sqlalchemy import create_engine, text


def run_migrations():
    migration_file = Path(__file__).parent.parent / "migrations" / "001_initial_schema.sql"
    if not migration_file.exists():
        print(f"Error: Migration file not found at {migration_file}")
        sys.exit(1)

    sql_content = migration_file.read_text(encoding="utf-8")
    db_uri = settings.SQLALCHEMY_DATABASE_URI

    print(f"Connecting to database: {db_uri.split('@')[-1] if '@' in db_uri else 'local'}")

    try:
        engine = create_engine(db_uri, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            # Execute migration SQL script
            print("Applying migration: 001_initial_schema.sql ...")
            conn.execute(text(sql_content))
            print("Successfully applied 001_initial_schema.sql.")
    except Exception as e:
        print(f"Migration execution note: {e}")
        print("If PostgreSQL is not running locally, configure DATABASE_URL in .env before deploying to Supabase/Production.")


if __name__ == "__main__":
    run_migrations()
