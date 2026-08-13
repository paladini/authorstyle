from __future__ import annotations

from pathlib import Path

import numpy as np

from authorstyle.embeddings.encoders import FakeStyleEncoder
from authorstyle.embeddings.service import EmbeddingService
from authorstyle.storage.embedding_store import EmbeddingStore


def test_embedding_cache(tmp_path: Path) -> None:
    store = EmbeddingStore(tmp_path)
    service = EmbeddingService(store)
    encoder = FakeStyleEncoder()
    texts = ["Sample text for caching."]
    vec1, refs1 = service.encode_style(encoder, texts)
    vec2, refs2 = service.encode_style(encoder, texts)
    assert refs1 == refs2
    assert np.allclose(vec1, vec2)


def test_fake_encoder_deterministic() -> None:
    enc = FakeStyleEncoder()
    a = enc.encode(["hello"])
    b = enc.encode(["hello"])
    assert np.allclose(a, b)
