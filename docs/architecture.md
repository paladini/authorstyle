# AuthorStyle Architecture

AuthorStyle is a local-first Python research CLI for learning and reproducing a consenting user's personal writing style from their own corpus.

## Principles

- **Style is not content.** Stylometric signals and style embeddings are separate from semantic/topic embeddings.
- **Mode/register is first-class.** Users may label documents with modes such as `technical`, `essay`, or `humor`.
- **Persona is deferred.** `PersonaClaim` schema exists, but automatic persona extraction is disabled in MVP.
- **Evidence-grounded profiles.** Style Card statements link to measured features and exemplar chunk IDs.
- **Document-level evaluation holdout.** Splits occur before chunking; near-duplicate families stay in one split.

## Pipeline

1. **Ingest** local `.md`, `.txt`, `.html`, `.docx` via loader adapters
2. **Canonicalize** conservatively (Unicode/platform normalization only)
3. **Deduplicate** exact (SHA-256) and near (SimHash) duplicates
4. **Split** canonical document families into train/validation/test
5. **Chunk** structurally by headings/paragraphs with adaptive size targets
6. **Extract** explicit stylometric features per chunk
7. **Encode** style and semantic embeddings through pluggable encoders
8. **Build** global and optional mode-specific `StyleProfile` objects
9. **Generate** K candidates with Style Card + exemplars under explicit privacy modes
10. **Score** style, content, naturalness, originality independently
11. **Evaluate** against held-out genuine author documents

## Storage

- SQLite: documents, chunks, profiles, runs, metadata
- NPZ files: cached embeddings keyed by encoder + content hash
- Profile home: `~/.authorstyle/profiles/<profile_id>/`

## Privacy modes

| Mode | Remote receives |
|------|-----------------|
| `LOCAL_ONLY` | nothing (mock/local providers only) |
| `REMOTE_PROFILE_ONLY` | task + Style Card |
| `REMOTE_EXEMPLARS` | task + Style Card + retrieved excerpts |

## Extension points (not in MVP)

- Automatic mode clustering
- Persona extraction with evidence
- StyleDistance / mStyleDistance adapters
- Vector database backends
- LoRA/QLoRA training
- Platform importers (Medium, Dev.to, Google Drive)
- Web UI

## What MVP does not claim

AuthorStyle models recurring stylistic patterns observed in the supplied corpus. It does not perfectly clone an author, reproduce personality, or guarantee topic-independent style transfer.
