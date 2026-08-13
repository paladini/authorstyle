from __future__ import annotations

import re

import numpy as np

from authorstyle.config import OriginalityConfig, ScoringWeights
from authorstyle.ingest.text_utils import tokenize_words
from authorstyle.models import (
    ContentPlan,
    GenerationCandidate,
    StyleProfile,
)
from authorstyle.stylometry.base import BaseStyleFeatureExtractor


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    return float(np.dot(a, b) / denom)


def score_style_embedding(candidate_vec: np.ndarray, profile: StyleProfile) -> float:
    if profile.style_embedding_centroid is None:
        return 0.5
    centroid = np.asarray(profile.style_embedding_centroid)
    return max(0.0, min(1.0, (cosine_similarity(candidate_vec, centroid) + 1) / 2))


def score_explicit_style(
    text: str,
    profile: StyleProfile,
) -> tuple[float, list[str]]:
    extractor = BaseStyleFeatureExtractor()
    features = extractor.extract(text).features
    flat: dict[str, float] = {}
    for key, value in features.items():
        if isinstance(value, dict):
            for sub_key, sub_val in value.items():
                flat[f"{key}.{sub_key}"] = float(sub_val)
        elif isinstance(value, (int, float)):
            flat[key] = float(value)

    diagnostics: list[str] = []
    scores: list[float] = []
    for key, value in flat.items():
        stat = profile.feature_statistics.get(key)
        if not stat or stat.median is None or stat.q25 is None or stat.q75 is None:
            continue
        if value < stat.q25:
            diagnostics.append(f"{key} below target distribution")
            scores.append(max(0.0, 1.0 - (stat.q25 - value) / (abs(stat.q25) + 1e-6)))
        elif value > stat.q75:
            diagnostics.append(f"{key} above target distribution")
            scores.append(max(0.0, 1.0 - (value - stat.q75) / (abs(stat.q75) + 1e-6)))
        else:
            scores.append(1.0)
    if not scores:
        return 0.5, diagnostics
    return float(np.mean(scores)), diagnostics


def score_content_adherence(text: str, plan: ContentPlan) -> float:
    score = 0.5
    if plan.thesis and plan.thesis.lower()[:40] in text.lower():
        score += 0.2
    if plan.sections:
        found = sum(1 for s in plan.sections if s.lower() in text.lower())
        score += 0.3 * (found / len(plan.sections))
    return min(1.0, score)


def score_naturalness(text: str) -> float:
    words = tokenize_words(text)
    if not words:
        return 0.0
    unique_ratio = len(set(words)) / len(words)
    sentence_count = max(1, len(re.split(r"[.!?]+", text)))
    avg_sent = len(words) / sentence_count
    penalty = 0.0
    if avg_sent < 4 or avg_sent > 45:
        penalty += 0.2
    if unique_ratio < 0.2:
        penalty += 0.2
    return max(0.0, min(1.0, 0.7 + unique_ratio * 0.3 - penalty))


def longest_common_substring(a: str, b: str) -> int:
    best = 0
    for i in range(len(a)):
        for j in range(i + 1, len(a) + 1):
            fragment = a[i:j]
            if len(fragment) > best and fragment in b:
                best = len(fragment)
    return best


def score_originality(
    text: str,
    corpus_texts: list[str],
    config: OriginalityConfig | None = None,
) -> tuple[float, list[str]]:
    config = config or OriginalityConfig()
    diagnostics: list[str] = []
    normalized = re.sub(r"\s+", " ", text.strip())
    worst = 0.0
    for source in corpus_texts:
        source_norm = re.sub(r"\s+", " ", source.strip())
        lcs = longest_common_substring(normalized.lower(), source_norm.lower())
        if lcs >= config.min_exact_span_chars:
            diagnostics.append(f"long exact overlap ({lcs} chars) with corpus source")
            worst = max(worst, lcs / max(len(normalized), 1))
        words = tokenize_words(normalized)
        source_words = tokenize_words(source_norm)
        if len(words) >= config.ngram_size:
            ngrams = {" ".join(words[i : i + config.ngram_size]) for i in range(len(words) - config.ngram_size + 1)}
            source_ngrams = {
                " ".join(source_words[i : i + config.ngram_size])
                for i in range(max(0, len(source_words) - config.ngram_size + 1))
            }
            overlap = len(ngrams & source_ngrams) / max(len(ngrams), 1)
            if overlap > config.max_ngram_overlap_ratio:
                diagnostics.append(f"high {config.ngram_size}-gram overlap ({overlap:.2f})")
                worst = max(worst, overlap)
    score = max(0.0, 1.0 - worst)
    return score, diagnostics


def aggregate_score(candidate: GenerationCandidate, weights: ScoringWeights) -> float:
    parts = {
        "style_embedding": candidate.style_embedding_score or 0.0,
        "explicit_style": candidate.explicit_style_score or 0.0,
        "content": candidate.content_score or 0.0,
        "naturalness": candidate.naturalness_score or 0.0,
        "originality": candidate.originality_score or 0.0,
    }
    total = (
        weights.style_embedding * parts["style_embedding"]
        + weights.explicit_style * parts["explicit_style"]
        + weights.content * parts["content"]
        + weights.naturalness * parts["naturalness"]
        + weights.originality * parts["originality"]
    )
    return float(total)


def calibration_percentile(
    candidate_distance: float,
    genuine_distances: list[float],
) -> float | None:
    if not genuine_distances:
        return None
    below = sum(1 for d in genuine_distances if d >= candidate_distance)
    return below / len(genuine_distances)
