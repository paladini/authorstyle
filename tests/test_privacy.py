from __future__ import annotations

from authorstyle.config import PrivacyMode
from authorstyle.generation.prompts import (
    apply_privacy_to_messages,
    build_writer_messages,
)
from authorstyle.models import ContentPlan, ProfileScope, StyleCard, StyleCardSection
from authorstyle.privacy.gate import audit_messages_for_privacy


def test_remote_profile_only_strips_exemplars() -> None:
    card = StyleCard(
        profile_id="p",
        scope=ProfileScope.GLOBAL,
        sections={"voice": StyleCardSection(title="Voice", summary="Measured rhythm.")},
    )
    messages = build_writer_messages(
        "Write about databases",
        ContentPlan(thesis="db"),
        card,
        ["SECRET CORPUS EXCERPT FROM USER PRIVATE DRAFT"],
        "technical",
    )
    redacted = apply_privacy_to_messages(messages, PrivacyMode.REMOTE_PROFILE_ONLY)
    combined = "\n".join(m.content for m in redacted)
    assert "SECRET CORPUS EXCERPT" not in combined
    audit_messages_for_privacy(
        redacted,
        PrivacyMode.REMOTE_PROFILE_ONLY,
        ["SECRET CORPUS EXCERPT FROM USER PRIVATE DRAFT"],
    )


def test_writer_prompt_includes_constraints() -> None:
    messages = build_writer_messages(
        "task",
        ContentPlan(thesis="task"),
        None,
        [],
        None,
    )
    assert "Never copy distinctive phrases" in messages[-1].content
