from __future__ import annotations

from pathlib import Path

from authorstyle.config import AppConfig
from authorstyle.generation.pipeline import GenerationPipeline
from authorstyle.services.analyze import AnalyzeService
from authorstyle.storage import ProfileStore

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "corpus"


def test_generation_pipeline_multi_candidate(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AUTHORSTYLE_HOME", str(tmp_path / "home"))
    profile = "genuser"
    config = AppConfig(num_candidates=3, generation_provider="mock")
    service = AnalyzeService(profile, config)
    service.ingest(FIXTURES / "en")
    service.analyze()

    run = GenerationPipeline(ProfileStore(profile), config).run(
        "Write about distributed databases", mode="technical"
    )
    assert len(run.candidates) == 3
    assert run.selected_candidate_index is not None
    assert all(c.aggregate_score is not None for c in run.candidates)
    assert run.candidates[run.selected_candidate_index].text


def test_mode_profile_when_train_data_exists(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AUTHORSTYLE_HOME", str(tmp_path / "home"))
    profile = "modeuser"
    service = AnalyzeService(profile)
    service.ingest(FIXTURES / "en")
    service.analyze()
    store = ProfileStore(profile)
    global_profile = store.sqlite.get_profile(profile, "global")
    assert global_profile is not None
    mode_profile = store.sqlite.get_profile(profile, "mode", "technical")
    train_docs = [
        d
        for d in store.sqlite.list_documents(profile)
        if (d.split or "train") == "train" and d.mode == "technical"
    ]
    if train_docs:
        assert mode_profile is not None
        assert mode_profile.mode == "technical"
