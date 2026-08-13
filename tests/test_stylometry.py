from __future__ import annotations

from authorstyle.stylometry.base import BaseStyleFeatureExtractor
from authorstyle.stylometry.stats import aggregate_feature_stats, robust_stats


def test_feature_extraction_returns_schema_version() -> None:
    extractor = BaseStyleFeatureExtractor()
    result = extractor.extract("Hello world! You write. Short line.\n\nAnother paragraph here.")
    assert result.schema_version == "1.0.0"
    assert "median_sentence_length" in result.features
    assert "punct_exclamation_per_100_words" in result.features


def test_robust_stats() -> None:
    stats = robust_stats([1.0, 2.0, 3.0, 4.0, 100.0])
    assert stats.count == 5
    assert stats.median == 3.0
    assert stats.q25 is not None


def test_profile_aggregation() -> None:
    stats = aggregate_feature_stats(
        [{"median_sentence_length": 10.0}, {"median_sentence_length": 20.0}]
    )
    assert stats["median_sentence_length"].median == 15.0
