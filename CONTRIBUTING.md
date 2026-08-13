# Contributing to AuthorStyle

Thank you for helping improve AuthorStyle.

This project is research-oriented, local-first, and privacy-aware. Contributions
are most valuable when they keep style analysis separate from content, preserve
evidence-grounded profiles, and remain testable offline.

## Development setup

1. Fork and clone the repository.
2. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment.
4. Install the package with development dependencies:

   ```bash
   python -m pip install -e ".[dev]"
   ```

5. Run the checks:

   ```bash
   python -m pytest
   python -m ruff check .
   authorstyle --help
   ```

## Contribution guidelines

- Keep code and documentation in English.
- Keep profiling local-first and offline by default.
- Do not add mandatory remote LLM calls or model downloads to core workflows.
- Maintain separation between style, mode/register, persona, and task/content.
- Add or update tests for behavior changes; core tests must run offline.
- Update `README.md`, `docs/`, or fixtures when user-facing behavior changes.
- Never commit private writing corpora or secrets.

## Pull request checklist

Before opening a pull request, make sure:

- Tests pass with `python -m pytest`.
- Linting passes with `python -m ruff check .`.
- The CLI loads with `authorstyle --help`.
- New public behavior is documented.
- The pull request explains why the change matters.

## Good first areas

- Additional document loaders and normalization edge cases.
- Language-specific stylometric heuristics without heavyweight NLP deps.
- Better near-duplicate detection tests and fixtures.
- Style Card readability improvements.
- Documentation and examples in English and Brazilian Portuguese.
- Optional encoder adapters behind extras (`[embeddings]`, `[nlp]`).

See [docs/ROADMAP.md](docs/ROADMAP.md) for larger planned extensions.
