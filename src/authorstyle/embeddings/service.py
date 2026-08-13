from __future__ import annotations

import numpy as np

from authorstyle.embeddings.encoders import SemanticEncoder, StyleEncoder
from authorstyle.ingest.text_utils import sha256_text
from authorstyle.storage.embedding_store import EmbeddingStore


class EmbeddingService:
    def __init__(self, store: EmbeddingStore) -> None:
        self.store = store

    def encode_style(
        self,
        encoder: StyleEncoder,
        texts: list[str],
    ) -> tuple[np.ndarray, list[str]]:
        refs: list[str] = []
        vectors: list[np.ndarray] = []
        for text in texts:
            content_sha = sha256_text(text)
            cached = self.store.get(encoder.name, encoder.version, content_sha)
            if cached is None:
                cached = encoder.encode([text])[0]
                self.store.put(encoder.name, encoder.version, content_sha, cached)
            refs.append(self.store.ref(encoder.name, encoder.version, content_sha))
            vectors.append(cached)
        return np.vstack(vectors), refs

    def encode_semantic(
        self,
        encoder: SemanticEncoder,
        texts: list[str],
    ) -> tuple[np.ndarray, list[str]]:
        refs: list[str] = []
        vectors: list[np.ndarray] = []
        for text in texts:
            content_sha = sha256_text(text)
            cached = self.store.get(encoder.name, encoder.version, content_sha)
            if cached is None:
                cached = encoder.encode([text])[0]
                self.store.put(encoder.name, encoder.version, content_sha, cached)
            refs.append(self.store.ref(encoder.name, encoder.version, content_sha))
            vectors.append(cached)
        return np.vstack(vectors), refs
