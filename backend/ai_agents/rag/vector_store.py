from __future__ import annotations

from typing import List, Tuple

try:  # Optional dependency
    import numpy as np
except Exception:  # pragma: no cover - fallback when numpy unavailable
    np = None


class VectorStore:
    """
    Minimal vector store abstraction using FAISS when available, with a
    numpy fallback to avoid hard failures in constrained environments.
    """

    def __init__(self, dim: int):
        self.dim = dim
        self._use_faiss = False
        self._index = None
        self._vectors = []
        try:
            import faiss  # type: ignore

            self._faiss = faiss
            self._index = faiss.IndexFlatIP(dim)
            self._use_faiss = True
        except Exception:
            self._faiss = None
            self._use_faiss = False

    def add(self, embeddings: np.ndarray):
        if embeddings is None:
            return
        if np is not None and hasattr(embeddings, "size") and embeddings.size == 0:
            return

        if self._use_faiss and self._index is not None and np is not None:
            self._index.add(embeddings.astype("float32"))
        else:
            if np is not None:
                self._vectors.extend(list(embeddings))
            else:
                # embeddings is list-of-lists fallback
                self._vectors.extend(embeddings)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[int, float]]:
        if np is not None and hasattr(query_embedding, "ndim") and query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        if (
            self._use_faiss
            and self._index is not None
            and hasattr(self._index, "ntotal")
            and self._index.ntotal > 0
            and np is not None
        ):
            scores, indices = self._index.search(query_embedding.astype("float32"), top_k)
            return [(int(idx), float(score)) for idx, score in zip(indices[0], scores[0]) if idx != -1]

        # fallback cosine similarity (numpy or pure python)
        if not self._vectors:
            return []

        if np is not None:
            matrix = np.vstack(self._vectors)
            q = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)
            matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9)
            sims = (matrix_norm @ q.T).flatten()
            top_indices = np.argsort(-sims)[:top_k]
            return [(int(i), float(sims[i])) for i in top_indices]

        # pure python fallback
        def cosine(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            na = sum(x * x for x in a) ** 0.5
            nb = sum(y * y for y in b) ** 0.5
            if na == 0 or nb == 0:
                return 0.0
            return dot / (na * nb)

        sims = [cosine(vec, query_embedding[0] if isinstance(query_embedding, list) and query_embedding and isinstance(query_embedding[0], list) else query_embedding) for vec in self._vectors]
        top_indices = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:top_k]
        return [(int(i), float(sims[i])) for i in top_indices]
