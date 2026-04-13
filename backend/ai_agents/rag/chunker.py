from __future__ import annotations

from typing import List


class CodeChunker:
    """
    Lightweight code splitter for RAG.

    Splits by characters with overlap to preserve context while keeping
    chunks small enough for embedding models.
    """

    def __init__(self, chunk_size: int = 1200, overlap: int = 120):
        self.chunk_size = max(200, chunk_size)
        self.overlap = max(0, min(overlap, self.chunk_size // 2))

    def split(self, code: str) -> List[str]:
        chunks: List[str] = []
        start = 0
        length = len(code)

        while start < length:
            end = min(length, start + self.chunk_size)
            chunk = code[start:end]
            chunks.append(chunk)
            if end == length:
                break
            start = end - self.overlap

        return chunks
