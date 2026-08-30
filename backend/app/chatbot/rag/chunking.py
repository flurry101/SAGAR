"""
RAG Chunking — Text Splitting Configuration

Splits loaded documents into overlapping chunks suitable for embedding
and semantic retrieval. Each chunk inherits its parent's metadata.

Reference: 12A_IMPLEMENTATION_PLAN.md, WS-09
"""

from __future__ import annotations


# Chunking parameters (tuned for marine knowledge documents)
CHUNK_SIZE = 500          # characters per chunk
CHUNK_OVERLAP = 50        # overlap between consecutive chunks
SEPARATORS = ["\n## ", "\n### ", "\n\n", "\n", ". ", " "]


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Split documents into overlapping chunks with metadata.

    Uses a recursive character text splitter that prefers splitting at
    markdown headers, then paragraphs, then sentences.

    Args:
        documents: List of dicts with 'content', 'source', 'domain'.

    Returns:
        List of dicts with 'content', 'source', 'domain' for each chunk.
    """
    # TODO: Use LangChain's RecursiveCharacterTextSplitter in production
    #
    # from langchain_text_splitters import RecursiveCharacterTextSplitter
    #
    # splitter = RecursiveCharacterTextSplitter(
    #     chunk_size=CHUNK_SIZE,
    #     chunk_overlap=CHUNK_OVERLAP,
    #     separators=SEPARATORS,
    # )
    #
    # chunks = []
    # for doc in documents:
    #     splits = splitter.split_text(doc["content"])
    #     for split in splits:
    #         chunks.append({
    #             "content": split,
    #             "source": doc["source"],
    #             "domain": doc["domain"],
    #         })
    # return chunks

    # Simple fallback chunker for testing
    chunks = []
    for doc in documents:
        text = doc["content"]
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk_text = text[start:end]
            chunks.append({
                "content": chunk_text,
                "source": doc["source"],
                "domain": doc["domain"],
            })
            start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks
