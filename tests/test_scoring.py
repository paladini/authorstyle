from __future__ import annotations

from authorstyle.config import OriginalityConfig
from authorstyle.scoring.metrics import score_originality

COPIED = (
    "Distributed databases need partition tolerance and careful consistency choices "
    "when the network fails and replication lag surprises your team during incidents."
)


def test_originality_detects_copied_passage() -> None:
    score, diagnostics = score_originality(
        COPIED,
        [COPIED + " extra"],
        OriginalityConfig(min_exact_span_chars=40),
    )
    assert score < 0.5
    assert diagnostics
