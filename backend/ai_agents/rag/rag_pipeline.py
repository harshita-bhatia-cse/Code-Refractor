from __future__ import annotations

from typing import List

from backend.ai_agents.rag.chunker import CodeChunker
from backend.ai_agents.rag.embedder import Embedder
from backend.ai_agents.rag.vector_store import VectorStore
from backend.ai_agents.rag.retriever import Retriever


class RAGPipeline:
    """
    Simple RAG pipeline for code refactoring:
      - chunk code
      - embed chunks
      - index in vector store
      - retrieve relevant chunks for a query
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        overlap: int | None = None,
        model_name: str | None = None,
    ):
        self.embedder = Embedder(model_name=model_name)
        self.chunker = CodeChunker(
            chunk_size=chunk_size or 1200, overlap=overlap or 120
        )
        self.store = VectorStore(self.embedder.dim)
        self._chunks: List[str] = []
        self._retriever: Retriever | None = None

    def index_code(self, code: str):
        self._chunks = self.chunker.split(code)
        if not self._chunks:
            return
        embeddings = self.embedder.embed_texts(self._chunks)
        self.store.add(embeddings)
        self._retriever = Retriever(self.store, self._chunks)

    def query(self, query_text: str, top_k: int = 5) -> List[str]:
        if not self._chunks:
            return []
        if self._retriever is None:
            return []
        q_emb = self.embedder.embed_texts([query_text])[0]
        return self._retriever.search(q_emb, top_k=top_k)
