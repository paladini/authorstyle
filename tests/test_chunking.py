from __future__ import annotations

from authorstyle.config import ChunkConfig
from authorstyle.ingest.chunking import structural_chunk


def test_structural_chunking_respects_paragraphs() -> None:
    text = (
        "# Title\n\nFirst paragraph with several words here.\n\n"
        "Second paragraph also present.\n\nThird paragraph completes the section."
    )
    chunks = structural_chunk("doc1", text, ChunkConfig(min_words=5, max_words=50))
    assert len(chunks) >= 1
    assert all(c.document_id == "doc1" for c in chunks)
    assert chunks[0].sequence_index == 0


def test_chunks_do_not_cross_documents() -> None:
    chunks_a = structural_chunk("a", "Paragraph one.\n\nParagraph two.")
    chunks_b = structural_chunk("b", "Different doc.")
    assert all(c.document_id == "a" for c in chunks_a)
    assert all(c.document_id == "b" for c in chunks_b)
