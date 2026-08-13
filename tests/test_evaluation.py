from __future__ import annotations

from pathlib import Path

from authorstyle.evaluation.runner import EvaluationService
from authorstyle.services.analyze import AnalyzeService

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "corpus"


def test_evaluation_outputs(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AUTHORSTYLE_HOME", str(tmp_path / "home"))
    profile = "evaluser"
    service = AnalyzeService(profile)
    service.ingest(FIXTURES / "en")
    service.analyze()
    result = EvaluationService(profile).run()
    assert "baselines" in result
    assert "generic" in result["baselines"]
    assert Path(result["paths"]["json"]).exists()
    assert Path(result["paths"]["md"]).exists()
