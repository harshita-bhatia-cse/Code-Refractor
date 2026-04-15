from __future__ import annotations

import hashlib
import os
from typing import Iterable

try:
    import numpy as np
except Exception:
    np = None


class Embedder:
    """
    Optimized embedding helper:
    - Uses sentence-transformers if available
    - Fast fallback hashing if not
    """

    _MODEL_CACHE = {}

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or os.getenv("LLM_EMBED_MODEL", "all-MiniLM-L6-v2")
        self._model = None
        self._dim = 384

        try:
            from sentence_transformers import SentenceTransformer
            cached_model = self._MODEL_CACHE.get(self.model_name)
            if cached_model is None:
                cached_model = SentenceTransformer(self.model_name)
                self._MODEL_CACHE[self.model_name] = cached_model
            self._model = cached_model
        except Exception:
            self._model = None

    @property
    def dim(self) -> int:
        return self._dim

    def _hash_embed(self, text: str):
        h = hashlib.sha256(text.encode("utf-8")).digest()
        needed = self._dim
        data = (h * ((needed // len(h)) + 1))[:needed]

        if np is None:
            arr = [float(b) for b in data]
            norm = sum(v * v for v in arr) ** 0.5
            return [v / norm for v in arr] if norm else arr

        arr = np.frombuffer(data, dtype=np.uint8).astype(np.float32)
        norm = np.linalg.norm(arr)
        return arr / norm if norm else arr

    def embed_texts(self, texts: Iterable[str]):
        texts = list(texts)

        # 🔥 LIMIT TEXT SIZE (important)
        texts = [t[:600] for t in texts]

        if self._model is not None:
            try:
                return self._model.encode(
                    texts,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    batch_size=8  # 🔥 faster batching
                )
            except Exception:
                pass

        embeddings = [self._hash_embed(t) for t in texts]

        if np is None:
            return embeddings

        return np.vstack(embeddings)
