"""
RAG Embeddings — Embedding Model Configuration

Configures the embedding model used for vectorizing knowledge documents
and queries. Uses Google's text-embedding-004 model via LangChain.

Reference: 12A_IMPLEMENTATION_PLAN.md, WS-09
"""

from __future__ import annotations

import os


# Embedding model configuration
EMBEDDING_MODEL = "models/text-embedding-004"
EMBEDDING_DIMENSIONS = 768  # text-embedding-004 output dimensions


def get_embedding_model():
    """Create and return the embedding model instance.

    Uses Google Generative AI Embeddings (text-embedding-004).

    Returns:
        A LangChain Embeddings instance.

    Raises:
        ValueError: If GOOGLE_API_KEY is not set.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable is required for embeddings. "
            "Set it in your .env file."
        )

    # TODO: Uncomment when langchain_google_genai is installed
    #
    # from langchain_google_genai import GoogleGenerativeAIEmbeddings
    #
    # return GoogleGenerativeAIEmbeddings(
    #     model=EMBEDDING_MODEL,
    #     google_api_key=api_key,
    # )

    # Stub: return None until dependency is installed
    return None
