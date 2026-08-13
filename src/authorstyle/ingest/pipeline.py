from __future__ import annotations

import uuid
from pathlib import Path

from authorstyle.config import ChunkConfig
from authorstyle.ingest.chunking import structural_chunk
from authorstyle.ingest.dedupe import exact_dedupe_key, near_duplicate_groups
from authorstyle.ingest.loaders import loader_for
from authorstyle.ingest.text_utils import (
    load_ignore_patterns,
    normalize_unicode,
    sha256_text,
    should_ignore,
)
from authorstyle.models import Chunk, Document

SUPPORTED_EXTENSIONS = {".md", ".txt", ".html", ".htm", ".docx"}


def _extract_metadata(loaded_meta: dict, path: Path) -> dict:
    title = loaded_meta.get("title")
    source = loaded_meta.get("source")
    publication_date = loaded_meta.get("date") or loaded_meta.get("publication_date")
    language = loaded_meta.get("language")
    mode = loaded_meta.get("mode")
    if mode == "auto":
        mode = None
    tags = loaded_meta.get("tags") or []
    published = loaded_meta.get("published")
    if published is not None and not isinstance(published, bool):
        published = bool(published)
    return {
        "title": title,
        "source": source,
        "publication_date": str(publication_date) if publication_date else None,
        "language": language,
        "mode": mode,
        "tags": tags if isinstance(tags, list) else [],
        "published": published,
    }


def discover_files(corpus_dir: Path) -> list[Path]:
    patterns = load_ignore_patterns(corpus_dir)
    files: list[Path] = []
    for path in sorted(corpus_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if should_ignore(path.relative_to(corpus_dir), patterns):
            continue
        files.append(path)
    return files


def ingest_corpus(
    profile_id: str,
    corpus_dir: Path,
    chunk_config: ChunkConfig | None = None,
) -> tuple[list[Document], list[Chunk]]:
    loaded: list[tuple[Path, str, dict]] = []
    for path in discover_files(corpus_dir):
        loader = loader_for(path)
        if not loader:
            continue
        doc = loader.load(path)
        meta = _extract_metadata(doc.metadata, path)
        loaded.append((path, doc.raw_text, meta))

    temp_docs: list[tuple[str, str, Path, dict]] = []
    for path, raw_text, meta in loaded:
        doc_id = str(uuid.uuid4())
        temp_docs.append((doc_id, raw_text, path, meta))

    groups = near_duplicate_groups([(d[0], d[1]) for d in temp_docs])
    canonical_map = {mid: g.canonical_id for g in groups for mid in g.member_ids}

    documents: list[Document] = []
    all_chunks: list[Chunk] = []
    seen_exact: dict[str, str] = {}

    for doc_id, raw_text, path, meta in temp_docs:
        normalized = normalize_unicode(raw_text)
        exact_key = exact_dedupe_key(normalized)
        canonical_id = canonical_map[doc_id]

        if exact_key in seen_exact:
            canonical_id = seen_exact[exact_key]
        else:
            seen_exact[exact_key] = canonical_id

        document = Document(
            id=doc_id,
            profile_id=profile_id,
            source_path=str(path),
            sha256=sha256_text(normalized),
            canonical_document_id=canonical_id,
            title=meta.get("title"),
            source=meta.get("source"),
            publication_date=meta.get("publication_date"),
            language=meta.get("language"),
            mode=meta.get("mode"),
            tags=meta.get("tags", []),
            published=meta.get("published"),
            raw_text=raw_text,
            normalized_text=normalized,
            metadata={"headings": meta.get("headings", [])},
        )
        documents.append(document)
        chunks = structural_chunk(document.id, normalized, chunk_config)
        all_chunks.extend(chunks)

    return documents, all_chunks
