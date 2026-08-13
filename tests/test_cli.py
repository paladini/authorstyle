from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from authorstyle.cli.app import app

runner = CliRunner()
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "corpus"


def test_cli_smoke(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AUTHORSTYLE_HOME", str(tmp_path / "home"))
    profile = "testuser"

    assert runner.invoke(app, ["init", profile]).exit_code == 0
    assert runner.invoke(app, ["ingest", profile, str(FIXTURES / "en")]).exit_code == 0
    assert runner.invoke(app, ["corpus", "stats", profile]).exit_code == 0
    assert runner.invoke(app, ["analyze", profile]).exit_code == 0
    assert runner.invoke(app, ["profile", "show", profile]).exit_code == 0
    write = runner.invoke(
        app,
        ["write", profile, "--prompt", "Write about databases", "--privacy", "LOCAL_ONLY"],
    )
    assert write.exit_code == 0
    assert "mock" in write.stdout.lower() or "generated" in write.stdout.lower()
    assert (tmp_path / "home" / "profiles" / profile).exists()


def test_portuguese_corpus_ingest(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AUTHORSTYLE_HOME", str(tmp_path / "home"))
    profile = "ptuser"
    assert runner.invoke(app, ["init", profile]).exit_code == 0
    assert runner.invoke(app, ["ingest", profile, str(FIXTURES / "pt-BR")]).exit_code == 0
    stats = runner.invoke(app, ["corpus", "stats", profile])
    assert stats.exit_code == 0
    assert "Documents" in stats.stdout
