"""
pgvector Retriever — Specialized Knowledge Retrieval

Connects to the Supabase pgvector table for semantic similarity search
with metadata filtering. Supports different knowledge domains:
- marine: PFZ, SST, chlorophyll, ocean currents
- safety: SVAS rules, vessel limits, hazard types
- regulations: MPA boundaries, seasonal bans, licensing
- glossary: Marine terminology definitions

Reference: 12A_IMPLEMENTATION_PLAN.md, WS-09
"""

from __future__ import annotations

from enum import Enum


class KnowledgeDomain(str, Enum):
    """Knowledge domains for metadata filtering."""
    MARINE = "marine"
    SAFETY = "safety"
    REGULATIONS = "regulations"
    GLOSSARY = "glossary"
    ALL = "all"


def get_retriever(
    domain: KnowledgeDomain = KnowledgeDomain.ALL,
    top_k: int = 5,
):
    """Create a pgvector retriever filtered by knowledge domain.

    Args:
        domain: Filter results to a specific knowledge domain.
                Use ALL for cross-domain search.
        top_k: Number of most-similar chunks to retrieve.

    Returns:
        A LangChain retriever instance backed by pgvector.

    Usage:
        retriever = get_retriever(domain=KnowledgeDomain.SAFETY, top_k=3)
        docs = retriever.invoke("What is the SVAS wave threshold?")
    """
    # TODO: Implement with Supabase pgvector
    #
    # from langchain_community.vectorstores import SupabaseVectorStore
    # from langchain_google_genai import GoogleGenerativeAIEmbeddings
    # from app.core.supabase_client import get_supabase
    #
    # embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    # supabase = get_supabase()
    #
    # vector_store = SupabaseVectorStore(
    #     client=supabase,
    #     embedding=embeddings,
    #     table_name="knowledge_chunks",
    #     query_name="match_knowledge_chunks",
    # )
    #
    # filter_kwargs = {}
    # if domain != KnowledgeDomain.ALL:
    #     filter_kwargs = {"filter": {"domain": domain.value}}
    #
    # return vector_store.as_retriever(
    #     search_type="similarity",
    #     search_kwargs={"k": top_k, **filter_kwargs},
    # )

    # Stub: return None until Supabase pgvector is configured
    return None
