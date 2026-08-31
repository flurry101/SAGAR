"""
pgvector & In-Memory Retriever — Specialized Knowledge Retrieval

Connects to the Supabase pgvector table for semantic similarity search
with metadata filtering. If Supabase is offline or unconfigured, falls back
to an in-memory keyword/TF-IDF retriever over all loaded documents and policy chunks.

Knowledge domains:
- marine: PFZ, SST, chlorophyll, ocean currents
- safety: SVAS rules, vessel limits, hazard types, Coast Guard distress SOP
- regulations: MPA boundaries, seasonal bans, licensing, Maritime Zones Act
- glossary: Marine terminology definitions
- conservation: Coral reefs, turtle sanctuaries, Wildlife Protection Act

Reference: 12A_IMPLEMENTATION_PLAN.md, WS-09
"""

from __future__ import annotations

import math
import re
from collections import Counter
from enum import Enum
from typing import List, Dict, Any, Optional

from langchain_core.documents import Document


class KnowledgeDomain(str, Enum):
    """Knowledge domains for metadata filtering."""
    MARINE = "marine"
    SAFETY = "safety"
    REGULATIONS = "regulations"
    GLOSSARY = "glossary"
    CONSERVATION = "conservation"
    ALL = "all"


class InMemoryKnowledgeRetriever:
    """In-memory TF-IDF / BM25 keyword retriever fallback for local & offline operation."""

    def __init__(self, domain: KnowledgeDomain = KnowledgeDomain.ALL, top_k: int = 5):
        self.domain = domain
        self.top_k = top_k
        self._docs: List[Document] = []
        self._doc_tokens: List[List[str]] = []
        self._doc_freqs: Counter = Counter()
        self._avg_doc_len: float = 0.0
        self._initialized: bool = False
        self._load_corpus()

    def _tokenize(self, text: str) -> List[str]:
        """Simple alphanumeric tokenizer."""
        return [w.lower() for w in re.findall(r"\b\w+\b", text) if len(w) > 1]

    def _load_corpus(self):
        if self._initialized:
            return

        from app.chatbot.rag.ingestion import load_documents
        from app.chatbot.rag.chunking import chunk_documents

        raw_docs = load_documents()
        raw_md = [d for d in raw_docs if not d.get("is_chunk")]
        pre_chunks = [d for d in raw_docs if d.get("is_chunk")]

        all_chunks = chunk_documents(raw_md)
        for p in pre_chunks:
            all_chunks.append({
                "content": p["content"],
                "source": p["source"],
                "domain": p["domain"],
                "metadata": p.get("metadata", {}),
            })

        total_len = 0
        for c in all_chunks:
            content = c.get("content", "")
            source = c.get("source", "unknown")
            domain = c.get("domain", "general")
            meta = {
                "source": source,
                "domain": domain,
                **c.get("metadata", {}),
            }

            doc = Document(page_content=content, metadata=meta)
            tokens = self._tokenize(content + " " + " ".join(str(v) for v in meta.values()))
            self._docs.append(doc)
            self._doc_tokens.append(tokens)

            unique_tokens = set(tokens)
            for t in unique_tokens:
                self._doc_freqs[t] += 1
            total_len += len(tokens)

        if self._docs:
            self._avg_doc_len = total_len / len(self._docs)
        self._initialized = True

    def invoke(self, query: str) -> List[Document]:
        """Score documents against query using BM25-style ranking and domain filtering."""
        self._load_corpus()
        if not self._docs or not query.strip():
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return self._docs[:self.top_k]

        N = len(self._docs)
        k1 = 1.5
        b = 0.75
        scored_docs = []

        for idx, (doc, tokens) in enumerate(zip(self._docs, self._doc_tokens)):
            # Filter by domain if specified
            if self.domain != KnowledgeDomain.ALL:
                doc_domain = doc.metadata.get("domain", "")
                if doc_domain != self.domain.value and self.domain.value not in doc_domain:
                    continue

            token_counts = Counter(tokens)
            doc_len = len(tokens)
            score = 0.0

            for qt in q_tokens:
                tf = token_counts.get(qt, 0)
                if tf > 0:
                    df = self._doc_freqs.get(qt, 1)
                    idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
                    denom = tf + k1 * (1.0 - b + b * (doc_len / max(self._avg_doc_len, 1.0)))
                    score += idf * (tf * (k1 + 1.0)) / max(denom, 1e-6)

                # Substring bonus for phrases or compound terms
                if qt in doc.page_content.lower():
                    score += 0.5

            if score > 0:
                scored_docs.append((score, doc))

        # Sort descending by score
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:self.top_k]]


def get_retriever(
    domain: KnowledgeDomain = KnowledgeDomain.ALL,
    top_k: int = 5,
):
    """Create a knowledge retriever with automatic pgvector-to-in-memory fallback.

    Args:
        domain: Filter results to a specific knowledge domain.
                Use ALL for cross-domain search.
        top_k: Number of most-similar chunks to retrieve.

    Returns:
        A retriever instance backed by pgvector or in-memory BM25.
    """
    import os
    supabase_url = os.environ.get("SUPABASE_DB_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
    google_api_key = os.environ.get("GOOGLE_API_KEY")

    if supabase_url and supabase_key and google_api_key:
        try:
            from langchain_community.vectorstores import SupabaseVectorStore
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            from supabase import create_client, Client

            embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
            supabase: Client = create_client(supabase_url, supabase_key)

            vector_store = SupabaseVectorStore(
                client=supabase,
                embedding=embeddings,
                table_name="knowledge_chunks",
                query_name="match_knowledge_chunks",
            )

            filter_kwargs = {}
            if domain != KnowledgeDomain.ALL:
                filter_kwargs = {"filter": {"domain": domain.value}}

            return vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": top_k, **filter_kwargs},
            )
        except Exception:
            pass

    # High-performance in-memory fallback
    return InMemoryKnowledgeRetriever(domain=domain, top_k=top_k)

