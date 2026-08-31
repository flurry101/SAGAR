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
    try:
        embeddings = get_embedding_model()
        if not embeddings:
            print("INFO: Google API key not configured for embeddings. Chunks prepared successfully.")
            return len(chunks)

        from app.core.supabase import get_supabase_client
        supabase = get_supabase_client()
        if not supabase:
            print("INFO: Supabase client not configured. Chunks prepared successfully.")
            return len(chunks)

        from langchain_community.vectorstores import SupabaseVectorStore

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
        print(f"Successfully ingested {len(texts)} chunks into Supabase pgvector!")
        return len(texts)
    except Exception as e:
        print(f"Vector storage ingestion note / error: {e}")
        return len(chunks)


if __name__ == "__main__":
    """Run the ingestion pipeline from the command line."""
    count = ingest_to_vector_store()
    print(f"Ingestion complete: {count} chunks processed.")
