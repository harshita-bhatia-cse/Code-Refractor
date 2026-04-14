from __future__ import annotations

from typing import List


class CodeChunker:
    """
    Optimized code splitter for RAG.

    Improvements:
    - Smaller chunks → faster embedding + LLM
    - Reduced overlap → less redundancy
    - Hard limit on chunks → prevents explosion on large files
    """

    def __init__(self, chunk_size: int = 600, overlap: int = 60, max_chunks: int = 50):
        self.chunk_size = max(200, chunk_size)
        self.overlap = max(0, min(overlap, self.chunk_size // 2))
        self.max_chunks = max_chunks  # 🔥 prevent too many chunks

    def split(self, code: str) -> List[str]:
        chunks: List[str] = []
        start = 0
        length = len(code)

        while start < length:
            end = min(length, start + self.chunk_size)
            chunk = code[start:end]

            chunks.append(chunk)

            # 🔥 STOP if too many chunks (prevents slow RAG)
            if len(chunks) >= self.max_chunks:
                break

            if end == length:
                break

            start = end - self.overlap

        return chunks