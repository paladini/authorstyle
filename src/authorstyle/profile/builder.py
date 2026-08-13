from __future__ import annotations

import uuid
from typing import Any

import numpy as np

from authorstyle.config import ModeEvidenceConfig
from authorstyle.models import (
    Chunk,
    Document,
    ExemplarSelection,
    FeatureStatistics,
    ProfileScope,
    StyleCard,
    StyleCardSection,
    StyleProfile,
)
from authorstyle.stylometry.stats import aggregate_feature_stats


def _flatten_features(features: dict[str, Any]) -> dict[str, float]:
    flat: dict[str, float] = {}
    for key, value in features.items():
        if isinstance(value, dict):
            for sub_key, sub_val in value.items():
                flat[f"{key}.{sub_key}"] = float(sub_val)
        elif isinstance(value, (int, float)):
            flat[key] = float(value)
    return flat


def build_style_card(
    profile_id: str,
    scope: ProfileScope,
    mode: str | None,
    stats: dict[str, FeatureStatistics],
    prototype_chunk_ids: list[str],
) -> StyleCard:
    def stat(name: str) -> FeatureStatistics | None:
        return stats.get(name)

    sections: dict[str, StyleCardSection] = {}

    msl = stat("median_sentence_length")
    if msl:
        sections["sentence_rhythm"] = StyleCardSection(
            title="Sentence rhythm",
            summary=(
                f"Typical sentences center around {msl.median:.1f} words "
                f"(q25={msl.q25:.1f}, q75={msl.q75:.1f})."
            ),
            evidence_metrics=["median_sentence_length"],
            evidence_chunk_ids=prototype_chunk_ids[:2],
        )

    mpl = stat("median_paragraph_length_words")
    if mpl:
        sections["paragraph_rhythm"] = StyleCardSection(
            title="Paragraph rhythm",
            summary=(
                f"Paragraphs often contain about {mpl.median:.1f} words "
                f"with one-sentence paragraphs at "
                f"{stats.get('one_sentence_paragraph_ratio', FeatureStatistics()).median or 0:.2f} ratio."
            ),
            evidence_metrics=["median_paragraph_length_words", "one_sentence_paragraph_ratio"],
            evidence_chunk_ids=prototype_chunk_ids[:2],
        )

    ttr = stat("type_token_ratio")
    if ttr:
        sections["lexical_tendencies"] = StyleCardSection(
            title="Lexical tendencies",
            summary=f"Lexical diversity (type/token) centers near {ttr.median:.3f}.",
            evidence_metrics=["type_token_ratio"],
        )

    punct_keys = [k for k in stats if k.startswith("punct_")]
    if punct_keys:
        top = sorted(punct_keys, key=lambda k: stats[k].median or 0, reverse=True)[:3]
        summary = ", ".join(f"{k.replace('punct_', '')}={stats[k].median:.2f}/100w" for k in top)
        sections["punctuation_typography"] = StyleCardSection(
            title="Punctuation and typography",
            summary=f"Notable punctuation rates: {summary}.",
            evidence_metrics=top,
        )

    sections["voice"] = StyleCardSection(
        title="Voice",
        summary="Reproduce measured rhythms and punctuation habits; avoid copying distinctive phrases.",
        evidence_metrics=["median_sentence_length", "type_token_ratio"],
        evidence_chunk_ids=prototype_chunk_ids[:1],
    )

    do = [
        "Match sentence and paragraph length distributions.",
        "Preserve punctuation and formatting tendencies.",
        "Use natural variation; do not exaggerate every measured trait.",
    ]
    avoid = [
        "Copy distinctive phrases from exemplars.",
        "Invent beliefs or biographical facts.",
        "Let topic vocabulary dominate stylistic imitation.",
    ]

    if scope == ProfileScope.MODE and mode:
        sections["mode_specific_behavior"] = StyleCardSection(
            title="Mode-specific behavior",
            summary=f"Profile calibrated for mode '{mode}' with supporting corpus evidence.",
            evidence_metrics=list(stats.keys())[:5],
            confidence="medium" if len(prototype_chunk_ids) < 5 else "high",
        )

    return StyleCard(
        profile_id=profile_id,
        scope=scope,
        mode=mode,
        sections=sections,
        do=do,
        avoid=avoid,
    )


def style_card_to_markdown(card: StyleCard) -> str:
    lines = [f"# Style Card — {card.profile_id}"]
    if card.mode:
        lines.append(f"Mode: {card.mode}")
    lines.append("")
    for _key, section in card.sections.items():
        lines.append(f"## {section.title}")
        lines.append(section.summary)
        if section.evidence_metrics:
            lines.append(f"Evidence metrics: {', '.join(section.evidence_metrics)}")
        lines.append("")
    lines.append("## Do")
    lines.extend(f"- {item}" for item in card.do)
    lines.append("")
    lines.append("## Avoid")
    lines.extend(f"- {item}" for item in card.avoid)
    return "\n".join(lines)


def select_exemplars(
    chunks: list[Chunk],
    documents: list[Document],
    style_vectors: np.ndarray,
    semantic_vectors: np.ndarray,
    centroid: np.ndarray,
    mode: str | None = None,
    max_exemplars: int = 5,
) -> list[ExemplarSelection]:
    doc_map = {d.id: d for d in documents}
    candidates: list[ExemplarSelection] = []
    style_dist = np.linalg.norm(style_vectors - centroid, axis=1)

    for idx, chunk in enumerate(chunks):
        doc = doc_map.get(chunk.document_id)
        if not doc:
            continue
        if mode and doc.mode != mode:
            continue
        reasons = ["stylistically near profile centroid"]
        if doc.mode:
            reasons.append(f"matches mode '{doc.mode}'")
        candidates.append(
            ExemplarSelection(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                reasons=reasons,
                score=float(-style_dist[idx]),
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    selected: list[ExemplarSelection] = []
    used_docs: set[str] = set()
    used_semantic: list[np.ndarray] = []

    for cand in candidates:
        if len(selected) >= max_exemplars:
            break
        if cand.document_id in used_docs:
            continue
        idx = next(i for i, c in enumerate(chunks) if c.id == cand.chunk_id)
        sem = semantic_vectors[idx]
        if used_semantic:
            sims = [float(np.dot(sem, u)) for u in used_semantic]
            if max(sims) > 0.92:
                continue
        cand.reasons.append("semantically diverse from other exemplars")
        cand.reasons.append("distinct canonical document")
        selected.append(cand)
        used_docs.add(cand.document_id)
        used_semantic.append(sem)
    return selected


def build_profile(
    profile_id: str,
    scope: ProfileScope,
    mode: str | None,
    documents: list[Document],
    chunks: list[Chunk],
    style_vectors: np.ndarray | None,
    corpus_hash: str,
    evidence: ModeEvidenceConfig | None = None,
) -> StyleProfile:
    evidence = evidence or ModeEvidenceConfig()
    warnings: list[str] = []

    if scope == ProfileScope.MODE:
        mode_docs = [d for d in documents if d.mode == mode]
        mode_chunks = [
            c for c in chunks if any(d.id == c.document_id for d in mode_docs)
        ]
        if len(mode_docs) < evidence.min_documents or len(mode_chunks) < evidence.min_chunks:
            warnings.append(
                f"Insufficient evidence for mode '{mode}'; profile shrinks toward global behavior."
            )
        documents = mode_docs or documents
        chunks = mode_chunks or chunks

    flat_sets = [_flatten_features(c.style_features) for c in chunks if c.style_features]
    stats = aggregate_feature_stats(flat_sets)

    centroid: list[float] | None = None
    dispersion: dict[str, float] | None = None
    if style_vectors is not None and len(style_vectors) > 0:
        c = np.mean(style_vectors, axis=0)
        centroid = c.tolist()
        dispersion = {
            "mean_distance": float(np.mean(np.linalg.norm(style_vectors - c, axis=1))),
            "std_distance": float(np.std(np.linalg.norm(style_vectors - c, axis=1))),
        }

    card = build_style_card(profile_id, scope, mode, stats, [])
    return StyleProfile(
        id=str(uuid.uuid4()),
        profile_id=profile_id,
        scope=scope,
        mode=mode,
        corpus_hash=corpus_hash,
        number_documents=len({d.canonical_document_id for d in documents}),
        number_chunks=len(chunks),
        feature_statistics=stats,
        style_embedding_centroid=centroid,
        style_embedding_distribution=dispersion,
        style_card=card,
        prototype_chunk_ids=[],
        warnings=warnings,
    )
