"""
RAG Ingestion — Document Loading & Embedding Pipeline

Loads markdown documents and structured JSON policy chunk corpora from the knowledge base,
attaches domain and legal metadata, and embeds them into Supabase pgvector.

Reference: 12A_IMPLEMENTATION_PLAN.md, WS-09
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Any

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
    "maritime_policy_chunks.json": "regulations",
}

CATEGORY_DOMAIN_MAP = {
    "Monsoon Fishing Ban": "regulations",
    "Maritime Safety & Distress": "safety",
    "Maritime Boundaries & Jurisdiction": "regulations",
    "Marine Conservation & Coral Reefs": "conservation",
}


def load_documents(docs_dir: Path | None = None) -> list[dict]:
    """Load all markdown documents and structured JSON chunk corpora from the knowledge base directory.

    Args:
        docs_dir: Path to the documents directory. Defaults to app/chatbot/documents/.

    Returns:
        List of dicts with 'content', 'source', 'domain', and optional 'metadata'.
    """
    docs_dir = docs_dir or DOCUMENTS_DIR
    documents = []

    # 1. Load Markdown documents
    for md_file in sorted(docs_dir.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
            domain = DOMAIN_MAP.get(md_file.name, "general")

            documents.append({
                "content": content,
                "source": md_file.name,
                "domain": domain,
                "is_chunk": False,
            })
        except Exception:
            pass

    # 2. Load JSON chunk corpora
    for json_file in sorted(docs_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            chunks = data.get("chunks", [])
            for chunk in chunks:
                chunk_id = chunk.get("id", "UNKNOWN")
                title = chunk.get("title", "")
                category = chunk.get("category", "")
                source = chunk.get("source", json_file.name)
                content = chunk.get("content", "")
                meta = chunk.get("metadata", {})

                domain = CATEGORY_DOMAIN_MAP.get(category, DOMAIN_MAP.get(json_file.name, "regulations"))

                # Format clean text including title and metadata hints for embedding and retrieval
                meta_context = []
                if "authority" in meta:
                    meta_context.append(f"Authority: {meta['authority']}")
                if "effective_dates" in meta:
                    meta_context.append(f"Effective Dates: {meta['effective_dates']}")
                if "emergency_frequencies" in meta:
                    meta_context.append(f"Frequencies: {meta['emergency_frequencies']}")
                if "zones_defined" in meta:
                    meta_context.append(f"Zones: {meta['zones_defined']}")
                if "protected_sanctuaries" in meta:
                    meta_context.append(f"Sanctuaries: {meta['protected_sanctuaries']}")

                header_prefix = f"### {title}\nCategory: {category}\n"
                if meta_context:
                    header_prefix += f"Details: {'; '.join(meta_context)}\n\n"

                enriched_content = f"{header_prefix}{content}"

                documents.append({
                    "content": enriched_content,
                    "source": f"{json_file.name}#{chunk_id}",
                    "domain": domain,
                    "is_chunk": True,
                    "metadata": {
                        "chunk_id": chunk_id,
                        "title": title,
                        "category": category,
                        "source": source,
                        **meta,
                    },
                })
        except Exception:
            pass

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

    # 2. Chunk documents (preserve pre-chunked JSON chunks)
    raw_md_docs = [d for d in documents if not d.get("is_chunk")]
    pre_chunked_docs = [d for d in documents if d.get("is_chunk")]

    chunks = chunk_documents(raw_md_docs)
    for p_doc in pre_chunked_docs:
        chunks.append({
            "content": p_doc["content"],
            "source": p_doc["source"],
            "domain": p_doc["domain"],
            "metadata": p_doc.get("metadata", {}),
        })

    print(f"Prepared {len(chunks)} chunks for knowledge embedding.")

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
        metadatas = [
            {"source": c["source"], "domain": c["domain"], **c.get("metadata", {})}
            for c in chunks
        ]

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

