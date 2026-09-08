# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/), and this
project uses semantic versioning.

## [0.2.1] - 2026-09-08

### Changed

- Bumped development and runtime dependency minimums (Dependabot batch):
  `beautifulsoup4`, `rich`, `sentence-transformers`, `ruff`, `hatchling`.
- Updated GitHub Actions: `actions/checkout` and `actions/setup-python`.

## [0.1.0] - 2026-08-12

### Added

- Initial Python package and `authorstyle` CLI.
- Local-first ingestion for `.md`, `.txt`, `.html`, `.docx`.
- YAML front matter support and `.authorstyleignore`.
- Exact and near-duplicate detection with provenance preservation.
- Structural chunking and document-level train/validation/test splits.
- Explicit stylometry with robust statistics.
- Pluggable style and semantic encoders (fake encoders for offline tests).
- Global and mode-specific StyleProfiles with evidence-grounded Style Cards.
- Style exemplar selection with diversity constraints.
- Multi-candidate generation with multi-metric scoring and originality guard.
- Optional diagnostic-driven revision pass.
- Held-out evaluation baselines and calibration percentiles.
- Privacy modes: `LOCAL_ONLY`, `REMOTE_PROFILE_ONLY`, `REMOTE_EXEMPLARS`.
- Tests, fixtures (English + Brazilian Portuguese), CI, and community docs.
