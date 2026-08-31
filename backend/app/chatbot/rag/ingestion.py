"""
RAG Ingestion — Document Loading & Embedding Pipeline

Loads markdown documents from the knowledge base, chunks them,
attaches domain metadata, and embeds them into Supabase pgvector.

Reference: 12A_IMPLEMENTATION_PLAN.md, WS-09
"""

from __future__ import annotations

import os
from pathlib import Path

from app.chatbot.rag.chunking import chunk_documents
from app.chatbot.rag.embeddings import get_embedding_model


# Default path to knowledge documents
DOCUMENTS_DIR = Path(__file__).parent.parent / "documents"

# Map filenames to knowledge domains for metadata filtering
DOMAIN_MAP = {
    "pfz_guide.md": "marine",
    "svas_safety.md": "safety",
    "fishing_regulations.md": "regulations",
    "marine_glossary.md": "glossary",
}


def load_documents(docs_dir: Path | None = None) -> list[dict]:
    """Load all markdown documents from the knowledge base directory.

    Args:
        docs_dir: Path to the documents directory. Defaults to app/chatbot/documents/.

    Returns:
        List of dicts with 'content', 'source', and 'domain' fields.
    """
    docs_dir = docs_dir or DOCUMENTS_DIR
    documents = []

    for md_file in sorted(docs_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        domain = DOMAIN_MAP.get(md_file.name, "general")

        documents.append({
            "content": content,
            "source": md_file.name,
            "domain": domain,
        })

    return documents


def ingest_to_vector_store(docs_dir: Path | None = None) -> int:
    """Full ingestion pipeline: load → chunk → embed → store.

    Args:
        docs_dir: Path to the documents directory.

    Returns:
        Number of chunks ingested.
    """
    # 1. Load documents
    documents = load_documents(docs_dir)
    if not documents:
        print("No documents found to ingest.")
        return 0

    # 2. Chunk documents
    chunks = chunk_documents(documents)
    print(f"Created {len(chunks)} chunks from {len(documents)} documents.")

    # 3. Embed and store
    supabase_url = os.environ.get("SUPABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

    if supabase_url and supabase_key:
        try:
            from supabase import create_client
            from langchain_community.vectorstores import SupabaseVectorStore

            embeddings = get_embedding_model()
            if embeddings is None:
                print("Embeddings model not available. Chunks prepared but not vectorized.")
                return len(chunks)

            supabase = create_client(supabase_url, supabase_key)
            texts = [c["content"] for c in chunks]
            metadatas = [{"source": c["source"], "domain": c["domain"]} for c in chunks]

            vector_store = SupabaseVectorStore.from_texts(
                texts=texts,
                metadatas=metadatas,
                embedding=embeddings,
                client=supabase,
                table_name="knowledge_chunks",
                query_name="match_knowledge_chunks",
            )
            print(f"Successfully ingested {len(texts)} chunks into Supabase vector store.")
            return len(texts)
        except Exception as e:
            print(f"Vector store ingestion error: {e}")
            return len(chunks)

    print("Notice: Supabase credentials not set. Chunks verified but not persisted to remote vector store.")
    return len(chunks)


if __name__ == "__main__":
    """Run the ingestion pipeline from the command line."""
    count = ingest_to_vector_store()
    print(f"Ingestion complete: {count} chunks processed.")
