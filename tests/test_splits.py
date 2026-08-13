from __future__ import annotations

from pathlib import Path

import pytest

from authorstyle.evaluation.split import assign_splits, validate_split_isolation
from authorstyle.ingest.pipeline import ingest_corpus

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "corpus"


def test_canonical_family_split_isolation() -> None:
    docs, _ = ingest_corpus("test", FIXTURES / "en")
    docs = assign_splits(docs, seed=42)
    validate_split_isolation(docs)


def test_split_isolation_fails_on_leak() -> None:
    docs, _ = ingest_corpus("test", FIXTURES / "en")
    leaked = docs.copy()
    leaked[0] = leaked[0].model_copy(update={"split": "train"})
    leaked[1] = leaked[1].model_copy(update={"split": "test"})
    if leaked[0].canonical_document_id == leaked[1].canonical_document_id:
        with pytest.raises(ValueError):
            validate_split_isolation(leaked)
