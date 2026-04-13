from __future__ import annotations

from typing import List

from backend.ai_agents.rag.vector_store import VectorStore


class Retriever:
    """
    Wraps VectorStore to return top-k text chunks for a query embedding.
    """

    def __init__(self, store: VectorStore, texts: List[str]):
        self.store = store
        self.texts = texts

    def search(self, query_embedding, top_k: int = 5) -> List[str]:
        results = self.store.search(query_embedding, top_k=top_k)
        return [self.texts[idx] for idx, _score in results if 0 <= idx < len(self.texts)]
