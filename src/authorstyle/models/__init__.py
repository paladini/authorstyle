from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ProfileScope(StrEnum):
    GLOBAL = "global"
    MODE = "mode"


class Document(BaseModel):
    id: str
    profile_id: str
    source_path: str
    sha256: str
    canonical_document_id: str
    title: str | None = None
    source: str | None = None
    publication_date: str | None = None
    language: str | None = None
    mode: str | None = None
    tags: list[str] = Field(default_factory=list)
    published: bool | None = None
    raw_text: str
    normalized_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    split: str | None = None


class Chunk(BaseModel):
    id: str
    document_id: str
    section: str | None = None
    sequence_index: int
    text: str
    word_count: int
    style_features: dict[str, Any] = Field(default_factory=dict)
    style_embedding_ref: str | None = None
    semantic_embedding_ref: str | None = None


class FeatureStatistics(BaseModel):
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    mad: float | None = None
    q10: float | None = None
    q25: float | None = None
    q75: float | None = None
    q90: float | None = None
    min: float | None = None
    max: float | None = None
    count: int = 0


class StyleCardSection(BaseModel):
    title: str
    summary: str
    evidence_metrics: list[str] = Field(default_factory=list)
    evidence_chunk_ids: list[str] = Field(default_factory=list)
    confidence: str = "high"


class StyleCard(BaseModel):
    schema_version: str = "1.0.0"
    profile_id: str
    scope: ProfileScope
    mode: str | None = None
    sections: dict[str, StyleCardSection] = Field(default_factory=dict)
    do: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)


class StyleProfile(BaseModel):
    id: str
    profile_id: str
    scope: ProfileScope
    mode: str | None = None
    schema_version: str = "1.0.0"
    corpus_hash: str
    number_documents: int
    number_chunks: int
    feature_statistics: dict[str, FeatureStatistics] = Field(default_factory=dict)
    style_embedding_centroid: list[float] | None = None
    style_embedding_distribution: dict[str, float] | None = None
    style_card: StyleCard | None = None
    prototype_chunk_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    warnings: list[str] = Field(default_factory=list)


class PersonaClaim(BaseModel):
    id: str
    profile_id: str
    category: str
    claim: str
    evidence_chunk_ids: list[str] = Field(default_factory=list)
    observed_at: datetime | None = None
    confidence: float = 0.0
    status: str = "inactive"


class ContentPlan(BaseModel):
    audience: str | None = None
    goal: str | None = None
    thesis: str | None = None
    sections: list[str] = Field(default_factory=list)
    facts_or_constraints: list[str] = Field(default_factory=list)
    desired_length: str | None = None
    language: str | None = None


class GenerationCandidate(BaseModel):
    text: str
    raw_provider_response: dict[str, Any] = Field(default_factory=dict)
    style_embedding_score: float | None = None
    explicit_style_score: float | None = None
    content_score: float | None = None
    naturalness_score: float | None = None
    originality_score: float | None = None
    aggregate_score: float | None = None
    diagnostics: list[str] = Field(default_factory=list)


class GenerationRun(BaseModel):
    id: str
    profile_id: str
    prompt: str
    mode: str | None = None
    persona_mode: str = "voice_only"
    provider: str
    model: str | None = None
    privacy_mode: str
    retrieved_style_chunk_ids: list[str] = Field(default_factory=list)
    retrieved_persona_claim_ids: list[str] = Field(default_factory=list)
    candidates: list[GenerationCandidate] = Field(default_factory=list)
    selected_candidate_index: int | None = None
    revision_history: list[str] = Field(default_factory=list)
    content_plan: ContentPlan | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeatureResult(BaseModel):
    schema_version: str = "1.0.0"
    features: dict[str, float | int | dict[str, float]] = Field(default_factory=dict)


class ExemplarSelection(BaseModel):
    chunk_id: str
    document_id: str
    reasons: list[str] = Field(default_factory=list)
    score: float = 0.0
