from __future__ import annotations

from typing import Protocol

import numpy as np

from authorstyle.models import FeatureResult, FeatureStatistics


class StyleFeatureExtractor(Protocol):
    schema_version: str

    def extract(self, text: str) -> FeatureResult:
        ...


def robust_stats(values: list[float]) -> FeatureStatistics:
    if not values:
        return FeatureStatistics(count=0)
    arr = np.asarray(values, dtype=float)
    q10, q25, q75, q90 = np.percentile(arr, [10, 25, 75, 90])
    median = float(np.median(arr))
    mad = float(np.median(np.abs(arr - median)))
    return FeatureStatistics(
        mean=float(np.mean(arr)),
        median=median,
        std=float(np.std(arr)),
        mad=mad,
        q10=float(q10),
        q25=float(q25),
        q75=float(q75),
        q90=float(q90),
        min=float(np.min(arr)),
        max=float(np.max(arr)),
        count=len(values),
    )


def aggregate_feature_stats(
    feature_sets: list[dict[str, float | int]],
) -> dict[str, FeatureStatistics]:
    if not feature_sets:
        return {}
    keys = feature_sets[0].keys()
    result: dict[str, FeatureStatistics] = {}
    for key in keys:
        values = [float(fs[key]) for fs in feature_sets if key in fs]
        if values:
            result[key] = robust_stats(values)
    return result
