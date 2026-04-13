from __future__ import annotations

import hashlib
import os
from typing import Iterable, List

try:  # Optional dependency
    import numpy as np
except Exception:  # pragma: no cover - fallback when numpy is unavailable
    np = None


class Embedder:
    """
    Embedding helper with graceful fallback if sentence-transformers
    is unavailable in the runtime environment.
    """

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or os.getenv("LLM_EMBED_MODEL", "all-MiniLM-L6-v2")
        self._model = None
        self._dim = 384  # default MiniLM dim; updated if model loads

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            # Try to infer embedding size
            test_vec = self._model.encode([""], convert_to_numpy=True)
            self._dim = int(test_vec.shape[1])
        except Exception:
            # Fallback: keep _model None, use hashing-based embedding
            self._model = None

    @property
    def dim(self) -> int:
        return self._dim

    def _hash_embed(self, text: str) -> np.ndarray:
        """
        Deterministic hash-based embedding for environments without
        sentence-transformers. Not semantically strong but prevents crashes.
        """
        h = hashlib.sha256(text.encode("utf-8")).digest()
        needed = self._dim
        data = (h * ((needed // len(h)) + 1))[:needed]
        if np is None:
            # list[float] fallback
            arr = [float(b) for b in data]
            norm = sum(v * v for v in arr) ** 0.5
            if norm:
                arr = [v / norm for v in arr]
            return arr
        arr = np.frombuffer(data, dtype=np.uint8).astype(np.float32)
        norm = np.linalg.norm(arr)
        return arr / norm if norm else arr

    def embed_texts(self, texts: Iterable[str]) -> np.ndarray:
        if self._model is not None:
            try:
                return self._model.encode(
                    list(texts), convert_to_numpy=True, normalize_embeddings=True
                )
            except Exception:
                pass

        # fallback path (numpy or list-of-list)
        embeddings = [self._hash_embed(t) for t in texts]
        if np is None:
            return embeddings  # type: ignore[return-value]
        return np.vstack(embeddings)
