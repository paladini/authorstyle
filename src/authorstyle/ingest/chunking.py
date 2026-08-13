from __future__ import annotations

import re
import uuid

from authorstyle.config import ChunkConfig
from authorstyle.ingest.text_utils import word_count
from authorstyle.models import Chunk


def _split_sections(text: str) -> list[tuple[str | None, str]]:
    sections: list[tuple[str | None, str]] = []
    current_heading: str | None = None
    buffer: list[str] = []

    for line in text.splitlines():
        if re.match(r"^#{1,6}\s+", line):
            if buffer:
                sections.append((current_heading, "\n".join(buffer).strip()))
                buffer = []
            current_heading = line.lstrip("#").strip()
        else:
            buffer.append(line)
    if buffer:
        sections.append((current_heading, "\n".join(buffer).strip()))
    if not sections:
        sections.append((None, text))
    return sections


def _split_paragraphs(section_text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", section_text) if p.strip()]


def structural_chunk(
    document_id: str,
    text: str,
    config: ChunkConfig | None = None,
) -> list[Chunk]:
    config = config or ChunkConfig()
    chunks: list[Chunk] = []
    seq = 0
    for heading, section_text in _split_sections(text):
        paragraphs = _split_paragraphs(section_text)
        group: list[str] = []
        group_words = 0

        def flush(section_heading: str | None = heading) -> None:
            nonlocal seq, group, group_words
            if not group:
                return
            chunk_text = "\n\n".join(group)
            chunks.append(
                Chunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    section=section_heading,
                    sequence_index=seq,
                    text=chunk_text,
                    word_count=word_count(chunk_text),
                )
            )
            seq += 1
            group = []
            group_words = 0

        for para in paragraphs:
            pw = word_count(para)
            if group and group_words + pw > config.max_words:
                flush()
            group.append(para)
            group_words += pw
            if group_words >= config.min_words:
                flush()
        flush()

    if not chunks and text.strip():
        chunks.append(
            Chunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                section=None,
                sequence_index=0,
                text=text.strip(),
                word_count=word_count(text),
            )
        )
    return chunks
