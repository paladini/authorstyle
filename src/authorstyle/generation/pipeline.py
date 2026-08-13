from __future__ import annotations

import uuid
from datetime import datetime

import numpy as np

from authorstyle.config import AppConfig
from authorstyle.embeddings.encoders import get_semantic_encoder, get_style_encoder
from authorstyle.embeddings.service import EmbeddingService
from authorstyle.generation.prompts import (
    apply_privacy_to_messages,
    build_content_plan,
    build_writer_messages,
)
from authorstyle.generation.providers import Message, get_provider
from authorstyle.models import GenerationCandidate, GenerationRun
from authorstyle.privacy.gate import (
    audit_messages_for_privacy,
    enforce_privacy_provider,
)
from authorstyle.profile.builder import select_exemplars
from authorstyle.scoring.metrics import (
    aggregate_score,
    score_content_adherence,
    score_explicit_style,
    score_naturalness,
    score_originality,
    score_style_embedding,
)
from authorstyle.storage import ProfileStore


def revision_prompt(candidate_text: str, diagnostics: list[str]) -> str:
    joined = "\n".join(f"- {d}" for d in diagnostics[:8])
    return f"""Revise only the stylistic deviations identified below.
Preserve meaning.
Do not exaggerate the requested traits.
Do not copy corpus passages.

DEVIATIONS
{joined}

TEXT
{candidate_text}
"""


class GenerationPipeline:
    def __init__(self, store: ProfileStore, config: AppConfig | None = None) -> None:
        self.store = store
        self.config = config or AppConfig.from_env()
        self.embedding_service = EmbeddingService(store.embeddings)

    def run(
        self,
        prompt: str,
        mode: str | None = None,
        num_candidates: int | None = None,
    ) -> GenerationRun:
        num_candidates = num_candidates or self.config.num_candidates
        provider = enforce_privacy_provider(
            self.config.privacy_mode,
            get_provider(self.config.generation_provider, self.config),
        )

        profiles = self.store.sqlite.list_profiles(self.store.profile_id)
        profile = next(
            (p for p in profiles if p.mode == mode),
            next((p for p in profiles if p.scope.value == "global"), None),
        )
        if profile is None:
            raise ValueError(
                f"No profile found for '{self.store.profile_id}'. Run 'authorstyle analyze' first."
            )

        documents = self.store.sqlite.list_documents(self.store.profile_id)
        chunks = [
            c
            for c in self.store.sqlite.list_chunks_for_profile(self.store.profile_id)
            if any(d.id == c.document_id and (d.split or "train") == "train" for d in documents)
        ]
        style_encoder = get_style_encoder(self.config.style_encoder)
        style_vectors, _ = self.embedding_service.encode_style(
            style_encoder, [c.text for c in chunks]
        )
        semantic_vectors, _ = self.embedding_service.encode_semantic(
            get_semantic_encoder(self.config.semantic_encoder), [c.text for c in chunks]
        )
        centroid = np.asarray(profile.style_embedding_centroid or np.zeros(32))
        exemplar_selections = select_exemplars(
            chunks,
            documents,
            style_vectors,
            semantic_vectors,
            centroid,
            mode=mode,
        )
        exemplar_texts = [
            next(c.text for c in chunks if c.id == e.chunk_id) for e in exemplar_selections
        ]

        content_plan = build_content_plan(prompt, language=documents[0].language if documents else None)
        include_exemplars = self.config.privacy_mode.value in (
            "REMOTE_EXEMPLARS",
            "LOCAL_ONLY",
        )
        messages = build_writer_messages(
            prompt,
            content_plan,
            profile.style_card,
            exemplar_texts if include_exemplars else [],
            mode,
        )
        if self.config.privacy_mode.value == "REMOTE_EXEMPLARS":
            messages = build_writer_messages(
                prompt, content_plan, profile.style_card, exemplar_texts, mode
            )
        elif self.config.privacy_mode.value == "REMOTE_PROFILE_ONLY":
            messages = build_writer_messages(prompt, content_plan, profile.style_card, [], mode)
        messages = apply_privacy_to_messages(messages, self.config.privacy_mode)
        audit_messages_for_privacy(messages, self.config.privacy_mode, exemplar_texts)

        candidates: list[GenerationCandidate] = []
        corpus_texts = [c.text for c in chunks]
        for i in range(num_candidates):
            result = provider.generate(messages, seed=42 + i)
            style_vec = style_encoder.encode([result.text])[0]
            explicit_score, diagnostics = score_explicit_style(result.text, profile)
            candidate = GenerationCandidate(
                text=result.text,
                raw_provider_response=result.raw,
                style_embedding_score=score_style_embedding(style_vec, profile),
                explicit_style_score=explicit_score,
                content_score=score_content_adherence(result.text, content_plan),
                naturalness_score=score_naturalness(result.text),
                originality_score=0.0,
                diagnostics=diagnostics,
            )
            orig_score, orig_diag = score_originality(result.text, corpus_texts, self.config.originality)
            candidate.originality_score = orig_score
            candidate.diagnostics.extend(orig_diag)
            candidate.aggregate_score = aggregate_score(candidate, self.config.scoring_weights)
            candidates.append(candidate)

        ranked = sorted(candidates, key=lambda c: c.aggregate_score or 0, reverse=True)
        selected = ranked[0]
        revision_history: list[str] = []

        if self.config.enable_revision and selected.diagnostics:
            revision_messages = messages + [
                Message("user", revision_prompt(selected.text, selected.diagnostics))
            ]
            revised = provider.generate(revision_messages, seed=99)
            style_vec = style_encoder.encode([revised.text])[0]
            explicit_score, diagnostics = score_explicit_style(revised.text, profile)
            revised_candidate = GenerationCandidate(
                text=revised.text,
                raw_provider_response=revised.raw,
                style_embedding_score=score_style_embedding(style_vec, profile),
                explicit_style_score=explicit_score,
                content_score=score_content_adherence(revised.text, content_plan),
                naturalness_score=score_naturalness(revised.text),
                originality_score=score_originality(revised.text, corpus_texts, self.config.originality)[0],
                diagnostics=diagnostics,
            )
            revised_candidate.aggregate_score = aggregate_score(
                revised_candidate, self.config.scoring_weights
            )
            if (revised_candidate.aggregate_score or 0) >= (selected.aggregate_score or 0):
                selected = revised_candidate
                revision_history.append("accepted revision")
            else:
                revision_history.append("kept original candidate")

        selected_index = candidates.index(selected) if selected in candidates else 0
        run = GenerationRun(
            id=str(uuid.uuid4()),
            profile_id=self.store.profile_id,
            prompt=prompt,
            mode=mode,
            persona_mode=self.config.persona_mode.value,
            provider=provider.name,
            model=getattr(provider, "model", None),
            privacy_mode=self.config.privacy_mode.value,
            retrieved_style_chunk_ids=[e.chunk_id for e in exemplar_selections],
            candidates=candidates if selected in candidates else candidates + [selected],
            selected_candidate_index=selected_index,
            revision_history=revision_history,
            content_plan=content_plan,
            timestamp=datetime.utcnow(),
        )
        self.store.sqlite.upsert_run(run)
        return run
