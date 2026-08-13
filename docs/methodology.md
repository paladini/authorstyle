# AuthorStyle Methodology

## Explicit stylometry

AuthorStyle extracts interpretable features from each chunk: sentence/paragraph rhythms, punctuation rates, lexical diversity, structural Markdown habits, and technical prose/code ratios. Features retain punctuation, capitalization, and function words.

Numeric features are summarized with robust statistics (median, MAD, quantiles) rather than means alone.

## Latent style embeddings

Style embeddings capture *how* text is written. They are stored separately from semantic embeddings, which capture *what* text is about. MVP uses pluggable encoders; tests use deterministic fake encoders.

## Topic/style entanglement

Even with separate embeddings, style signals may correlate with recurring subjects (e.g., database tutorials). Evaluation reports surface document source/mode metadata and warn against over-interpreting topic-specific vocabulary as style.

## Global vs mode profiles

A global profile aggregates all training documents. Mode profiles aggregate documents with matching front-matter `mode`. Insufficient mode evidence triggers warnings and fallback toward global behavior.

## Document-level holdout

Splits assign entire canonical document families to train, validation, or test. Chunks from the same document never appear in multiple splits. Near-duplicate reposts share a canonical family and therefore share a split.

## Multi-objective generation evaluation

Generated candidates receive independent scores:

- latent style similarity
- explicit stylometric fit
- content adherence to the content plan
- naturalness heuristics
- originality vs corpus overlap

An aggregate score applies configurable weights but never hides component scores.

## Originality protection

Candidates are checked for long exact spans and word n-gram overlap against the corpus. Overlap diagnostics name nearest risks conservatively.

## Calibration

Held-out genuine author documents establish an empirical distribution of style distances. Generated text is reported relative to that distribution (percentile), not arbitrary thresholds.
