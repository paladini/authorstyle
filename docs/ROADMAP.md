# Roadmap

AuthorStyle MVP is complete. Future work is organized by research value and
community demand. Nothing here is committed to a timeline.

## Near term

- Real style embedding adapters (StyleDistance / mStyleDistance) behind `[embeddings]`
- Sentence-transformers semantic encoder as optional backend
- Ollama/local LLM generation provider
- Improved mode evidence warnings and fallback UX
- More corpus fixtures and evaluation reports

## Medium term

- Automatic mode clustering from unlabeled corpora
- PersonaClaim extraction with evidence and consent gates
- Style-eliciting-prompt decoder interface
- Human evaluation import hooks
- Cross-topic evaluation utilities and reporting

## Long term

- LoRA / QLoRA adapter training for style transfer
- Semantic-neutralization training pairs
- Platform importers (Medium, Dev.to, Google Drive exports)
- Vector database backends (optional; SQLite/NPZ remains default)
- Web UI for profile inspection and evaluation review

## Explicitly out of scope

- Impersonation of third parties without consent
- Automatic psychological, political, or religious inference
- Hosted SaaS backend, user accounts, or billing
- Claims of perfect author cloning

## How to influence the roadmap

- Open a [feature request](https://github.com/paladini/authorstyle/issues/new?template=feature_request.yml)
- Comment on existing issues with use cases and constraints
- Contribute prototypes behind optional extras to keep core offline-first

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.
