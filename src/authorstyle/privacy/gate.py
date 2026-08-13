from __future__ import annotations

from authorstyle.config import PrivacyMode
from authorstyle.generation.providers import GenerationProvider


def enforce_privacy_provider(
    privacy_mode: PrivacyMode,
    provider: GenerationProvider,
) -> GenerationProvider:
    if privacy_mode == PrivacyMode.LOCAL_ONLY and provider.name != "mock":
        raise ValueError(
            "LOCAL_ONLY privacy mode permits only local/mock providers. "
            "Set AUTHORSTYLE_PRIVACY_MODE or choose provider=mock."
        )
    return provider


def audit_messages_for_privacy(
    messages: list,
    privacy_mode: PrivacyMode,
    corpus_excerpt_markers: list[str] | None = None,
) -> None:
    if privacy_mode != PrivacyMode.REMOTE_PROFILE_ONLY:
        return
    corpus_excerpt_markers = corpus_excerpt_markers or []
    combined = "\n".join(getattr(m, "content", str(m)) for m in messages)
    if "STYLE EXEMPLARS\n(none" not in combined and "STYLE EXEMPLARS" in combined:
        exemplar_section = combined.split("STYLE EXEMPLARS", 1)[1]
        if len(exemplar_section.strip()) > 80:
            raise ValueError("REMOTE_PROFILE_ONLY must not include raw exemplars")
    for marker in corpus_excerpt_markers:
        if marker and marker in combined:
            raise ValueError("REMOTE_PROFILE_ONLY must not include raw corpus text")
