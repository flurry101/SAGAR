"""
Knowledge Base Ingestion CLI for SAGAR Copilot.

Loads markdown documents from backend/app/chatbot/documents/, chunks them,
embeds them with Gemini text-embedding-004, and stores them into pgvector/Supabase.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.chatbot.rag.ingestion import ingest_to_vector_store


def main():
    print("=" * 60)
    print("SAGAR / ORCA Marine Knowledge Ingestion")
    print("=" * 60)
    count = ingest_to_vector_store()
    print("=" * 60)
    print(f"Ingestion process finished. Total chunks: {count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
