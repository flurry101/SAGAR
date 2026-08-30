"""
Knowledge Tools — RAG Retrieval (Layer 1)

These tools allow the Copilot to search the curated marine knowledge base
for answers about PFZ, regulations, safety, and marine science.

Reference: 08_AI_ML_AGENTIC_ARCHITECTURE.md, Section 28 — Layer 1
"""

from __future__ import annotations

from langchain_core.tools import tool


@tool
def search_marine_knowledge(query: str) -> str:
    """Search the marine knowledge base for information.

    Use this for general fisherman knowledge questions like:
    - "What is PFZ?"
    - "What does chlorophyll concentration mean for fishing?"
    - "What are the SVAS safety rules?"
    - "What fishing regulations apply near MPAs?"
    - "What is the best fishing season?"

    This searches embedded documents including:
    - PFZ Guide (how PFZ works, how to interpret PFZ maps)
    - SVAS Safety Rules (vessel safety, wave thresholds)
    - Fishing Regulations (MPA rules, seasonal bans)
    - Marine Glossary (SST, chlorophyll, swell, HAB definitions)

    Args:
        query: The fisherman's question in natural language.

    Returns:
        Relevant knowledge passages with source citations.
    """
    # TODO: Implement pgvector retrieval
    # from app.chatbot.retrieval.retriever import get_retriever
    # retriever = get_retriever()
    # docs = retriever.invoke(query)
    # return "\n\n".join([
    #     f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
    #     for doc in docs
    # ])

    return (
        f"[Knowledge search stub] Query: '{query}'\n"
        "This would search the pgvector knowledge base in production.\n"
        "Available knowledge domains: PFZ, SVAS Safety, Fishing Regulations, Marine Glossary."
    )


# Convenience list for registration
KNOWLEDGE_TOOLS = [
    search_marine_knowledge,
]
