# AuthorStyle

[![CI](https://github.com/paladini/authorstyle/actions/workflows/ci.yml/badge.svg)](https://github.com/paladini/authorstyle/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

**Learn and reproduce your personal writing style from your own corpus — locally,
with evidence, and without fine-tuning.**

AuthorStyle is a research-oriented Python CLI. It ingests your historical writing,
extracts interpretable stylometric fingerprints and pluggable style embeddings,
builds evidence-grounded Style Profiles, and generates text through a
multi-candidate pipeline with held-out evaluation.

This is **not** a "paste your docs into an LLM prompt" wrapper.

## Why AuthorStyle?

Most style tools conflate **how you write** with **what you write about**. That
leads to profiles that recognize your favorite topics instead of your voice.

AuthorStyle separates:

| Concept | Meaning |
|---------|---------|
| **Style** | Sentence rhythm, punctuation, structure, formatting |
| **Mode** | How style shifts by context (technical, essay, humor, …) |
| **Persona** | What you believe or know (schema only in MVP; extraction deferred) |
| **Task** | What the current prompt needs to communicate |

Core principles:

- **Local-first** — raw corpus stays on your machine; profiling needs no remote LLM
- **Evidence-grounded** — Style Card statements link to metrics and exemplars
- **Explainable scores** — style, content, naturalness, originality reported separately
- **Honest evaluation** — document-level holdout; no "perfect clone" claims

AuthorStyle extends the local-first spirit of [idioleto](https://github.com/paladini/idioleto)
with a fuller research pipeline: deduplication, mode profiles, dual embeddings,
multi-metric reranking, and calibration against genuine held-out writing.

## How it works

```
Corpus (.md, .txt, .html, .docx)
  → ingest + dedupe + structural chunking
  → explicit stylometry + style/semantic embeddings
  → global + mode StyleProfiles + Style Card
  → retrieve exemplars → generate K candidates → score + rerank
  → optional revision → evaluate against held-out docs
```

See [docs/architecture.md](docs/architecture.md) and [docs/methodology.md](docs/methodology.md)
for design and scientific details.

## Quick start

### Install

```bash
git clone https://github.com/paladini/authorstyle.git
cd authorstyle
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
pip install -e ".[dev]"
```

Windows PowerShell:

```powershell
git clone https://github.com/paladini/authorstyle.git
cd authorstyle
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### Run

```bash
authorstyle init fernando
authorstyle ingest fernando ./fixtures/corpus/en
authorstyle analyze fernando
authorstyle profile show fernando
authorstyle write fernando --prompt "Write about distributed databases"
authorstyle evaluate fernando
```

Profiles are stored under `~/.authorstyle/profiles/<profile_id>/`.

## Example output

After `authorstyle analyze`, a Style Card is written to your profile directory:

```markdown
## Sentence rhythm
Typical sentences center around 18.0 words (q25=12.0, q75=24.0).
Evidence metrics: median_sentence_length

## Punctuation and typography
Notable punctuation rates: comma=4.20/100w, question=1.10/100w
Evidence metrics: punct_comma_per_100_words, punct_question_per_100_words

## Do
- Match sentence and paragraph length distributions.
- Preserve punctuation and formatting tendencies.

## Avoid
- Copy distinctive phrases from exemplars.
- Invent beliefs or biographical facts.
```

Every generation run stores candidates, component scores, retrieved exemplars,
and provider metadata for reproducibility.

## Privacy

| Mode | What remote providers may receive |
|------|-----------------------------------|
| `LOCAL_ONLY` | Nothing — only local/mock providers permitted |
| `REMOTE_PROFILE_ONLY` | Task + Style Card (no raw corpus excerpts) |
| `REMOTE_EXEMPLARS` | Task + Style Card + selected exemplar passages |

Copy `.env.example` to `.env` for optional remote generation settings.
Never commit secrets or private corpora.

## Corpus format

Supported files: `.md`, `.txt`, `.html`, `.docx`

Optional YAML front matter in Markdown:

```yaml
---
title: "My article"
date: 2025-04-02
source: devto
language: pt-BR
mode: technical
published: true
tags:
  - databases
---
```

Use `.authorstyleignore` in the corpus directory to skip paths (gitignore-style).

## Commands

| Command | Purpose |
|---------|---------|
| `authorstyle init <profile>` | Create profile workspace |
| `authorstyle ingest <profile> <dir>` | Ingest corpus |
| `authorstyle corpus stats <profile>` | Corpus statistics |
| `authorstyle analyze <profile>` | Build profiles + Style Card |
| `authorstyle profile show <profile>` | Show profile summary |
| `authorstyle exemplars <profile>` | Show style exemplars |
| `authorstyle write <profile> --prompt "..."` | Generate text |
| `authorstyle evaluate <profile>` | Held-out evaluation |
| `authorstyle runs show <run_id>` | Inspect generation run |

## Evaluation

Evaluation uses **document-level held-out splits** — chunks from the same document
never appear in both profile and test sets.

Baselines compared: `generic`, `card`, `examples`, `hybrid`, `full`.

Reports include style embedding distance, explicit stylometric fit, content
adherence, originality, and **calibration percentiles** relative to genuine
held-out author writing.

## Limitations

AuthorStyle **models recurring stylistic patterns observed in the supplied corpus**.
It does not:

- perfectly clone your writing
- guarantee topic-independent style transfer
- infer personality or beliefs automatically (persona extraction is future work)

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

- [Roadmap](docs/ROADMAP.md)
- [Support](SUPPORT.md)
- [Security](SECURITY.md)
- [Changelog](CHANGELOG.md)

## License

MIT — see [LICENSE](LICENSE).
