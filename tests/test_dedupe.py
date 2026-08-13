from __future__ import annotations

from pathlib import Path

from authorstyle.ingest.dedupe import exact_dedupe_key, near_duplicate_groups
from authorstyle.ingest.pipeline import ingest_corpus

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "corpus"


def test_exact_duplicate_with_different_front_matter() -> None:
    docs, _ = ingest_corpus("test", FIXTURES / "en")
    reposts = [d for d in docs if "article_a" in Path(d.source_path).name]
    assert len(reposts) == 2
    keys = {exact_dedupe_key(d.normalized_text) for d in reposts}
    assert len(keys) == 1


def test_genuinely_different_articles_not_merged() -> None:
    docs, _ = ingest_corpus("test", FIXTURES / "en")
    families = {d.canonical_document_id for d in docs}
    assert len(families) >= 2


def test_near_duplicate_grouping() -> None:
    text_a = "Distributed databases need partition tolerance and careful consistency choices."
    text_b = "Distributed databases need partition tolerance and careful consistency choices!"
    text_c = "Completely unrelated content about cooking pasta with garlic."
    groups = near_duplicate_groups(
        [("a", text_a), ("b", text_b), ("c", text_c)],
        threshold_bits=8,
    )
    merged = next(g for g in groups if "a" in g.member_ids)
    assert "b" in merged.member_ids
    assert "c" not in merged.member_ids
