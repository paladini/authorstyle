from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from authorstyle.models import (
    Chunk,
    Document,
    GenerationRun,
    StyleProfile,
)


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    canonical_document_id TEXT NOT NULL,
                    title TEXT,
                    source TEXT,
                    publication_date TEXT,
                    language TEXT,
                    mode TEXT,
                    tags TEXT,
                    published INTEGER,
                    raw_text TEXT NOT NULL,
                    normalized_text TEXT NOT NULL,
                    metadata TEXT,
                    split TEXT
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    section TEXT,
                    sequence_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    word_count INTEGER NOT NULL,
                    style_features TEXT,
                    style_embedding_ref TEXT,
                    semantic_embedding_ref TEXT
                );
                CREATE TABLE IF NOT EXISTS profiles (
                    id TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    mode TEXT,
                    data TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL,
                    data TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_documents_profile ON documents(profile_id);
                CREATE INDEX IF NOT EXISTS idx_documents_canonical ON documents(canonical_document_id);
                CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
                """
            )

    def set_meta(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                (key, value),
            )

    def get_meta(self, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else None

    def upsert_document(self, doc: Document) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    doc.id,
                    doc.profile_id,
                    doc.source_path,
                    doc.sha256,
                    doc.canonical_document_id,
                    doc.title,
                    doc.source,
                    doc.publication_date,
                    doc.language,
                    doc.mode,
                    json.dumps(doc.tags),
                    None if doc.published is None else int(doc.published),
                    doc.raw_text,
                    doc.normalized_text,
                    json.dumps(doc.metadata),
                    doc.split,
                ),
            )

    def list_documents(self, profile_id: str) -> list[Document]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM documents WHERE profile_id = ? ORDER BY source_path",
                (profile_id,),
            ).fetchall()
        return [self._row_to_document(r) for r in rows]

    def _row_to_document(self, row: sqlite3.Row) -> Document:
        return Document(
            id=row["id"],
            profile_id=row["profile_id"],
            source_path=row["source_path"],
            sha256=row["sha256"],
            canonical_document_id=row["canonical_document_id"],
            title=row["title"],
            source=row["source"],
            publication_date=row["publication_date"],
            language=row["language"],
            mode=row["mode"],
            tags=json.loads(row["tags"] or "[]"),
            published=None if row["published"] is None else bool(row["published"]),
            raw_text=row["raw_text"],
            normalized_text=row["normalized_text"],
            metadata=json.loads(row["metadata"] or "{}"),
            split=row["split"],
        )

    def upsert_chunk(self, chunk: Chunk) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO chunks VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    chunk.id,
                    chunk.document_id,
                    chunk.section,
                    chunk.sequence_index,
                    chunk.text,
                    chunk.word_count,
                    json.dumps(chunk.style_features),
                    chunk.style_embedding_ref,
                    chunk.semantic_embedding_ref,
                ),
            )

    def list_chunks(self, document_ids: list[str] | None = None) -> list[Chunk]:
        with self._connect() as conn:
            if document_ids:
                placeholders = ",".join("?" * len(document_ids))
                rows = conn.execute(
                    f"SELECT * FROM chunks WHERE document_id IN ({placeholders}) ORDER BY sequence_index",
                    document_ids,
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM chunks ORDER BY sequence_index"
                ).fetchall()
        return [self._row_to_chunk(r) for r in rows]

    def list_chunks_for_profile(self, profile_id: str) -> list[Chunk]:
        docs = self.list_documents(profile_id)
        if not docs:
            return []
        return self.list_chunks([d.id for d in docs])

    def _row_to_chunk(self, row: sqlite3.Row) -> Chunk:
        return Chunk(
            id=row["id"],
            document_id=row["document_id"],
            section=row["section"],
            sequence_index=row["sequence_index"],
            text=row["text"],
            word_count=row["word_count"],
            style_features=json.loads(row["style_features"] or "{}"),
            style_embedding_ref=row["style_embedding_ref"],
            semantic_embedding_ref=row["semantic_embedding_ref"],
        )

    def upsert_profile(self, profile: StyleProfile) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO profiles (id, profile_id, scope, mode, data) VALUES (?,?,?,?,?)",
                (
                    profile.id,
                    profile.profile_id,
                    profile.scope.value,
                    profile.mode,
                    profile.model_dump_json(),
                ),
            )

    def list_profiles(self, profile_id: str) -> list[StyleProfile]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT data FROM profiles WHERE profile_id = ?",
                (profile_id,),
            ).fetchall()
        return [StyleProfile.model_validate_json(r["data"]) for r in rows]

    def get_profile(self, profile_id: str, scope: str, mode: str | None = None) -> StyleProfile | None:
        with self._connect() as conn:
            if mode:
                row = conn.execute(
                    "SELECT data FROM profiles WHERE profile_id = ? AND scope = ? AND mode = ?",
                    (profile_id, scope, mode),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT data FROM profiles WHERE profile_id = ? AND scope = ? AND mode IS NULL",
                    (profile_id, scope),
                ).fetchone()
        return StyleProfile.model_validate_json(row["data"]) if row else None

    def upsert_run(self, run: GenerationRun) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO runs (id, profile_id, data) VALUES (?,?,?)",
                (run.id, run.profile_id, run.model_dump_json()),
            )

    def get_run(self, run_id: str) -> GenerationRun | None:
        with self._connect() as conn:
            row = conn.execute("SELECT data FROM runs WHERE id = ?", (run_id,)).fetchone()
        return GenerationRun.model_validate_json(row["data"]) if row else None

    def corpus_stats(self, profile_id: str) -> dict[str, Any]:
        docs = self.list_documents(profile_id)
        chunks = self.list_chunks_for_profile(profile_id)
        modes: dict[str, int] = {}
        for doc in docs:
            key = doc.mode or "unlabeled"
            modes[key] = modes.get(key, 0) + 1
        return {
            "documents": len(docs),
            "chunks": len(chunks),
            "words": sum(c.word_count for c in chunks),
            "modes": modes,
            "canonical_families": len({d.canonical_document_id for d in docs}),
        }
