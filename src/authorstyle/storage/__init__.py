from __future__ import annotations

from pathlib import Path

from authorstyle.config import profile_dir
from authorstyle.storage.embedding_store import EmbeddingStore
from authorstyle.storage.sqlite_store import SQLiteStore


class ProfileStore:
    def __init__(self, profile_id: str) -> None:
        self.profile_id = profile_id
        self.root = profile_dir(profile_id)
        self.root.mkdir(parents=True, exist_ok=True)
        self.sqlite = SQLiteStore(self.root / "meta.sqlite")
        self.embeddings = EmbeddingStore(self.root / "embeddings")

    def style_card_json_path(self) -> Path:
        return self.root / "style_card.json"

    def style_card_md_path(self) -> Path:
        return self.root / "style_card.md"

    def evaluations_dir(self) -> Path:
        path = self.root / "evaluations"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def runs_dir(self) -> Path:
        path = self.root / "runs"
        path.mkdir(parents=True, exist_ok=True)
        return path
