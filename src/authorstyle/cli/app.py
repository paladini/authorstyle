from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from authorstyle.config import AppConfig, PrivacyMode, profile_dir
from authorstyle.evaluation.runner import EvaluationService
from authorstyle.generation.pipeline import GenerationPipeline
from authorstyle.services.analyze import AnalyzeService
from authorstyle.storage import ProfileStore

app = typer.Typer(
    no_args_is_help=True,
    help="AuthorStyle — learn and reproduce personal writing style from your corpus.",
)
console = Console()


@app.command("init")
def init_profile(profile_id: str) -> None:
    """Create a new profile workspace."""
    root = profile_dir(profile_id)
    root.mkdir(parents=True, exist_ok=True)
    ProfileStore(profile_id)
    console.print(f"[green]Initialized profile[/green] {profile_id} at {root}")


@app.command("ingest")
def ingest(profile_id: str, corpus_path: Path) -> None:
    """Ingest a local corpus directory."""
    if not corpus_path.exists():
        raise typer.BadParameter(f"Corpus path not found: {corpus_path}")
    service = AnalyzeService(profile_id)
    service.ingest(corpus_path)
    stats = ProfileStore(profile_id).sqlite.corpus_stats(profile_id)
    console.print(f"Ingested {stats['documents']} documents, {stats['chunks']} chunks.")


corpus_app = typer.Typer(no_args_is_help=True)
app.add_typer(corpus_app, name="corpus")


@corpus_app.command("stats")
def corpus_stats(profile_id: str) -> None:
    """Show corpus statistics."""
    stats = ProfileStore(profile_id).sqlite.corpus_stats(profile_id)
    table = Table(title=f"Corpus stats — {profile_id}")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Documents", str(stats["documents"]))
    table.add_row("Chunks", str(stats["chunks"]))
    table.add_row("Words", str(stats["words"]))
    table.add_row("Canonical families", str(stats["canonical_families"]))
    for mode, count in stats["modes"].items():
        table.add_row(f"Mode: {mode}", str(count))
    console.print(table)


@app.command("analyze")
def analyze(profile_id: str) -> None:
    """Build style profiles and Style Card."""
    AnalyzeService(profile_id).analyze()
    console.print(f"[green]Analysis complete[/green] for {profile_id}")


profile_app = typer.Typer(no_args_is_help=True)
app.add_typer(profile_app, name="profile")


@profile_app.command("show")
def profile_show(
    profile_id: str,
    mode: str | None = typer.Option(None, help="Show mode-specific profile"),
) -> None:
    """Display profile summary."""
    store = ProfileStore(profile_id)
    if mode:
        profile = store.sqlite.get_profile(profile_id, "mode", mode)
    else:
        profile = store.sqlite.get_profile(profile_id, "global")
    if not profile:
        raise typer.BadParameter(
            f"Profile not found. Run 'authorstyle analyze {profile_id}' first."
        )
    console.print(f"Scope: {profile.scope.value} mode={profile.mode}")
    console.print(
        f"Documents: {profile.number_documents} Chunks: {profile.number_chunks}"
    )
    for warning in profile.warnings:
        console.print(f"[yellow]Warning:[/yellow] {warning}")
    if profile.style_card:
        for section in profile.style_card.sections.values():
            console.print(f"- {section.title}: {section.summary}")


@app.command("exemplars")
def exemplars(
    profile_id: str,
    mode: str | None = typer.Option(None, help="Filter by mode"),
) -> None:
    """Show representative style exemplars."""
    store = ProfileStore(profile_id)
    profile = (
        store.sqlite.get_profile(profile_id, "mode", mode)
        if mode
        else store.sqlite.get_profile(profile_id, "global")
    )
    if not profile:
        raise typer.BadParameter("Profile not found.")
    chunks = {c.id: c for c in store.sqlite.list_chunks_for_profile(profile_id)}
    for chunk_id in profile.prototype_chunk_ids:
        chunk = chunks.get(chunk_id)
        if chunk:
            console.print(chunk.text[:240] + ("..." if len(chunk.text) > 240 else ""))
            console.print("")


@app.command("write")
def write(
    profile_id: str,
    prompt: str = typer.Option(..., help="Writing task prompt"),
    mode: str | None = typer.Option(None, help="Target writing mode"),
    candidates: int = typer.Option(3, help="Number of candidates"),
    privacy: Annotated[
        PrivacyMode,
        typer.Option(help="Privacy mode"),
    ] = PrivacyMode.LOCAL_ONLY,
) -> None:
    """Generate style-conditioned text."""
    config = AppConfig.from_env()
    config.privacy_mode = privacy
    config.num_candidates = candidates
    run = GenerationPipeline(ProfileStore(profile_id), config).run(prompt, mode=mode)
    selected = run.candidates[run.selected_candidate_index or 0]
    console.print(selected.text)
    console.print(f"\n[dim]Run ID: {run.id}[/dim]")


@app.command("evaluate")
def evaluate(profile_id: str) -> None:
    """Run held-out evaluation baselines."""
    result = EvaluationService(profile_id).run()
    console.print(f"Evaluation written to {result['paths']['json']}")


runs_app = typer.Typer(no_args_is_help=True)
app.add_typer(runs_app, name="runs")


@runs_app.command("show")
def runs_show(run_id: str) -> None:
    """Show a generation run."""
    from authorstyle.config import get_home

    found = None
    profiles_root = get_home() / "profiles"
    if profiles_root.exists():
        for profile_path in profiles_root.iterdir():
            store = ProfileStore(profile_path.name)
            run = store.sqlite.get_run(run_id)
            if run:
                found = run
                break
    if not found:
        raise typer.BadParameter(
            f"Run {run_id} not found. Check the run ID from 'authorstyle write'."
        )
    console.print(found.model_dump_json(indent=2))
