"""In-process Chroma vector store backed by Gemini embeddings."""

from __future__ import annotations

import chromadb
from google.genai import types

from core.config import get_settings
from core.gemini_client import get_genai_client
from data.sample_regulations import SAMPLE_REGULATIONS

# Module-level collection populated during app startup.
_collection: chromadb.Collection | None = None


async def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using the configured Gemini embedding model."""
    settings = get_settings()
    client = get_genai_client()

    # Prototype: embed one-by-one for simplicity; batch API would scale better.
    embeddings: list[list[float]] = []
    for text in texts:
        result = await client.aio.models.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            contents=f"Retrieve documents relevant to this workplace safety query: {text}",
            config=types.EmbedContentConfig(
                output_dimensionality=settings.GEMINI_EMBEDDING_DIMENSION
            ),
        )
        embeddings.append(list(result.embeddings[0].values))
    return embeddings


async def initialize_regulation_store() -> None:
    """Embed sample regulations and load them into an in-process Chroma collection."""
    global _collection

    # Embedded Chroma — no separate server. For production, use a managed vector DB.
    chroma_client = chromadb.Client()
    _collection = chroma_client.get_or_create_collection(
        name="safety_regulations",
        metadata={"hnsw:space": "cosine"},
    )

    if _collection.count() > 0:
        return

    ids = [f"reg-{i}" for i in range(len(SAMPLE_REGULATIONS))]
    embeddings = await _embed_texts(SAMPLE_REGULATIONS)
    _collection.add(
        ids=ids,
        documents=SAMPLE_REGULATIONS,
        embeddings=embeddings,
    )


async def retrieve_relevant_regulations(query: str, k: int = 3) -> list[str]:
    """Return the top-k regulation snippets most similar to the query."""
    if _collection is None:
        raise RuntimeError("Regulation store not initialized — call initialize_regulation_store() first")

    query_embeddings = await _embed_texts([query])
    results = _collection.query(
        query_embeddings=query_embeddings,
        n_results=min(k, _collection.count()),
    )

    documents = results.get("documents")
    if not documents or not documents[0]:
        return []

    return list(documents[0])
