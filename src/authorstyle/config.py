from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class PrivacyMode(StrEnum):
    LOCAL_ONLY = "LOCAL_ONLY"
    REMOTE_PROFILE_ONLY = "REMOTE_PROFILE_ONLY"
    REMOTE_EXEMPLARS = "REMOTE_EXEMPLARS"


class PersonaMode(StrEnum):
    VOICE_ONLY = "voice_only"
    VOICE_PLUS_PERSONA = "voice_plus_persona"


class ScoringWeights(BaseModel):
    style_embedding: float = 0.25
    explicit_style: float = 0.25
    content: float = 0.25
    naturalness: float = 0.15
    originality: float = 0.10


class ChunkConfig(BaseModel):
    min_words: int = 80
    max_words: int = 400


class SplitConfig(BaseModel):
    train_ratio: float = 0.7
    validation_ratio: float = 0.15
    test_ratio: float = 0.15
    seed: int = 42


class ModeEvidenceConfig(BaseModel):
    min_documents: int = 3
    min_chunks: int = 5


class OriginalityConfig(BaseModel):
    min_exact_span_chars: int = 80
    ngram_size: int = 5
    max_ngram_overlap_ratio: float = 0.35
    near_duplicate_threshold: float = 0.85


class AppConfig(BaseModel):
    privacy_mode: PrivacyMode = PrivacyMode.LOCAL_ONLY
    persona_mode: PersonaMode = PersonaMode.VOICE_ONLY
    scoring_weights: ScoringWeights = Field(default_factory=ScoringWeights)
    chunk: ChunkConfig = Field(default_factory=ChunkConfig)
    split: SplitConfig = Field(default_factory=SplitConfig)
    mode_evidence: ModeEvidenceConfig = Field(default_factory=ModeEvidenceConfig)
    originality: OriginalityConfig = Field(default_factory=OriginalityConfig)
    num_candidates: int = 3
    enable_revision: bool = True
    style_encoder: str = "fake"
    semantic_encoder: str = "fake"
    generation_provider: str = "mock"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    @classmethod
    def from_env(cls) -> AppConfig:
        privacy = os.getenv("AUTHORSTYLE_PRIVACY_MODE", "LOCAL_ONLY")
        return cls(
            privacy_mode=PrivacyMode(privacy),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )


def get_home() -> Path:
    return Path(os.getenv("AUTHORSTYLE_HOME", Path.home() / ".authorstyle"))


def profile_dir(profile_id: str) -> Path:
    return get_home() / "profiles" / profile_id
