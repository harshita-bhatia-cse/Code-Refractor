from __future__ import annotations

from typing import List, Tuple

try:
    import numpy as np
except Exception:
    np = None


class VectorStore:

    def __init__(self, dim: int):
        self.dim = dim
        self._vectors = []
        self._index = None
        self._use_faiss = False

        try:
            import faiss
            self._index = faiss.IndexFlatIP(dim)
            self._use_faiss = True
        except Exception:
            self._use_faiss = False

    def add(self, embeddings):
        if embeddings is None:
            return

        if self._use_faiss and np is not None:
            self._index.add(embeddings.astype("float32"))
        else:
            if np is not None:
                self._vectors.extend(list(embeddings))
            else:
                self._vectors.extend(embeddings)

    def search(self, query_embedding, top_k: int = 2) -> List[Tuple[int, float]]:
        if np is not None and hasattr(query_embedding, "ndim") and query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # 🔥 FAISS path
        if self._use_faiss and self._index is not None and self._index.ntotal > 0:
            scores, indices = self._index.search(query_embedding.astype("float32"), top_k)
            return [(int(i), float(s)) for i, s in zip(indices[0], scores[0]) if i != -1]

        # 🔥 NUMPY fallback (optimized)
        if not self._vectors:
            return []

        if np is not None:
            matrix = np.vstack(self._vectors)

            q = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)
            matrix = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9)

            sims = matrix @ q.T
            sims = sims.flatten()

            top_idx = np.argsort(-sims)[:top_k]
            return [(int(i), float(sims[i])) for i in top_idx]

        # 🔥 pure python fallback
        def cosine(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            na = sum(x * x for x in a) ** 0.5
            nb = sum(y * y for y in b) ** 0.5
            return dot / (na * nb + 1e-9)

        sims = [cosine(vec, query_embedding) for vec in self._vectors]
        top_idx = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:top_k]

        return [(int(i), float(sims[i])) for i in top_idx]