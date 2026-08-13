from __future__ import annotations

import random

from authorstyle.models import Document


def assign_splits(
    documents: list[Document],
    train_ratio: float = 0.7,
    validation_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> list[Document]:
    assert abs(train_ratio + validation_ratio + test_ratio - 1.0) < 1e-6

    families: dict[str, list[Document]] = {}
    for doc in documents:
        families.setdefault(doc.canonical_document_id, []).append(doc)

    family_ids = sorted(families.keys())
    rng = random.Random(seed)
    rng.shuffle(family_ids)

    n = len(family_ids)
    train: set[str] = set()
    val: set[str] = set()
    test: set[str] = set()

    if n == 1:
        train.add(family_ids[0])
    elif n == 2:
        train.add(family_ids[0])
        test.add(family_ids[1])
    else:
        n_train = max(1, int(n * train_ratio))
        n_val = max(0, int(n * validation_ratio))
        if n_train + n_val >= n:
            n_train = max(1, n - 1)
            n_val = 0
        train.update(family_ids[:n_train])
        val.update(family_ids[n_train : n_train + n_val])
        test.update(family_ids[n_train + n_val :])

    updated: list[Document] = []
    for doc in documents:
        if doc.canonical_document_id in test:
            split = "test"
        elif doc.canonical_document_id in val:
            split = "validation"
        else:
            split = "train"
        updated.append(doc.model_copy(update={"split": split}))
    return updated


def validate_split_isolation(documents: list[Document]) -> None:
    family_splits: dict[str, set[str]] = {}
    for doc in documents:
        family_splits.setdefault(doc.canonical_document_id, set()).add(doc.split or "")
    for family, splits in family_splits.items():
        non_empty = {s for s in splits if s}
        if len(non_empty) > 1:
            raise ValueError(
                f"Canonical family {family} appears in multiple splits: {non_empty}"
            )
