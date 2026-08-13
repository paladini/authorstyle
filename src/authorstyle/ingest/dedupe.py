from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from authorstyle.ingest.text_utils import canonicalize_for_dedupe, sha256_text


@dataclass
class DedupeGroup:
    canonical_id: str
    canonical_sha256: str
    member_ids: list[str]


def exact_dedupe_key(text: str) -> str:
    return sha256_text(canonicalize_for_dedupe(text))


def _shingles(text: str, k: int = 5) -> set[str]:
    words = re.findall(r"\b\w+\b", text.lower(), flags=re.UNICODE)
    if len(words) < k:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + k]) for i in range(len(words) - k + 1)}


def _simhash(text: str, bits: int = 64) -> int:
    shingles = _shingles(text)
    if not shingles:
        return 0
    vector = [0] * bits
    for shingle in shingles:
        h = int(hashlib.md5(shingle.encode()).hexdigest(), 16)
        for i in range(bits):
            vector[i] += 1 if (h >> i) & 1 else -1
    fingerprint = 0
    for i, val in enumerate(vector):
        if val >= 0:
            fingerprint |= 1 << i
    return fingerprint


def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def near_duplicate_groups(
    items: list[tuple[str, str]],
    threshold_bits: int = 6,
) -> list[DedupeGroup]:
    """Group near duplicates deterministically by simhash."""
    if not items:
        return []
    sorted_items = sorted(items, key=lambda x: x[0])
    groups: list[DedupeGroup] = []
    assigned: set[str] = set()

    for doc_id, text in sorted_items:
        if doc_id in assigned:
            continue
        canonical_id = doc_id
        canonical_sha = exact_dedupe_key(text)
        member_ids = [doc_id]
        assigned.add(doc_id)
        fp = _simhash(canonicalize_for_dedupe(text))

        for other_id, other_text in sorted_items:
            if other_id in assigned:
                continue
            other_fp = _simhash(canonicalize_for_dedupe(other_text))
            if hamming_distance(fp, other_fp) <= threshold_bits:
                member_ids.append(other_id)
                assigned.add(other_id)

        groups.append(
            DedupeGroup(
                canonical_id=canonical_id,
                canonical_sha256=canonical_sha,
                member_ids=sorted(member_ids),
            )
        )
    return groups
