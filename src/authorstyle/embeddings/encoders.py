from __future__ import annotations

from typing import Protocol

import numpy as np


class StyleEncoder(Protocol):
    name: str
    version: str

    def encode(self, texts: list[str]) -> np.ndarray:
        ...


class SemanticEncoder(Protocol):
    name: str
    version: str

    def encode(self, texts: list[str]) -> np.ndarray:
        ...


class FakeStyleEncoder:
    name = "fake-style"
    version = "1.0.0"

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            seed = sum(ord(c) for c in text[:200]) % 997
            rng = np.random.default_rng(seed)
            vec = rng.normal(size=32)
            vec = vec / (np.linalg.norm(vec) + 1e-8)
            vectors.append(vec)
        return np.vstack(vectors)


class FakeSemanticEncoder:
    name = "fake-semantic"
    version = "1.0.0"

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            words = text.lower().split()[:50]
            seed = hash(" ".join(words)) % 997
            rng = np.random.default_rng(seed)
            vec = rng.normal(size=32)
            vec = vec / (np.linalg.norm(vec) + 1e-8)
            vectors.append(vec)
        return np.vstack(vectors)


def get_style_encoder(name: str) -> StyleEncoder:
    if name in ("fake", "fake-style"):
        return FakeStyleEncoder()
    raise ValueError(f"Unknown style encoder: {name}")


def get_semantic_encoder(name: str) -> SemanticEncoder:
    if name in ("fake", "fake-semantic"):
        return FakeSemanticEncoder()
    raise ValueError(f"Unknown semantic encoder: {name}")
