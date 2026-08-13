from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np


class EmbeddingStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _key_path(self, encoder_name: str, version: str, content_sha: str) -> Path:
        safe = hashlib.sha256(f"{encoder_name}:{version}:{content_sha}".encode()).hexdigest()
        return self.root / encoder_name / version / f"{safe}.npz"

    def get(self, encoder_name: str, version: str, content_sha: str) -> np.ndarray | None:
        path = self._key_path(encoder_name, version, content_sha)
        if not path.exists():
            return None
        data = np.load(path)
        return data["embedding"]

    def put(
        self,
        encoder_name: str,
        version: str,
        content_sha: str,
        embedding: np.ndarray,
    ) -> str:
        path = self._key_path(encoder_name, version, content_sha)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, embedding=embedding.astype(np.float32))
        return str(path.relative_to(self.root))

    def ref(self, encoder_name: str, version: str, content_sha: str) -> str:
        return f"{encoder_name}:{version}:{content_sha}"
