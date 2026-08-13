from __future__ import annotations

from authorstyle.config import PrivacyMode
from authorstyle.generation.providers import Message
from authorstyle.models import ContentPlan, StyleCard

WRITER_CONSTRAINTS = """
Reproduce stylistic patterns, not sentences.
Never copy distinctive phrases or passages from the exemplars.
Do not invent beliefs, experiences, opinions, or biographical facts for the profile owner.
Preserve natural variation; do not exaggerate every detected stylistic trait.
Task/content correctness outranks superficial imitation.
""".strip()


def build_content_plan(prompt: str, language: str | None = None) -> ContentPlan:
    return ContentPlan(
        audience="general reader",
        goal="address the user task",
        thesis=prompt,
        sections=["opening", "body", "closing"],
        facts_or_constraints=[prompt],
        desired_length="medium",
        language=language,
    )


def build_writer_messages(
    prompt: str,
    content_plan: ContentPlan,
    style_card: StyleCard | None,
    exemplars: list[str],
    mode: str | None,
    persona_evidence: list[str] | None = None,
) -> list[Message]:
    card_text = ""
    if style_card:
        card_text = "\n".join(
            f"{section.title}: {section.summary}" for section in style_card.sections.values()
        )
    exemplar_text = "\n\n---\n\n".join(exemplars) if exemplars else "(none)"
    persona_text = "\n".join(persona_evidence or []) or "(none — voice only)"

    system = f"""You are a writing assistant reproducing stylistic patterns from an author profile.

{WRITER_CONSTRAINTS}
"""
    user = f"""TASK
{prompt}

CONTENT PLAN
{content_plan.model_dump_json(indent=2)}

TARGET MODE
{mode or 'global'}

STYLE CARD
{card_text or '(none)'}

STYLE EXEMPLARS
{exemplar_text}

OPTIONAL PERSONA EVIDENCE
{persona_text}

CONSTRAINTS
{WRITER_CONSTRAINTS}
"""
    return [Message(role="system", content=system), Message(role="user", content=user)]


def apply_privacy_to_messages(
    messages: list[Message],
    privacy_mode: PrivacyMode,
) -> list[Message]:
    if privacy_mode == PrivacyMode.REMOTE_PROFILE_ONLY:
        redacted: list[Message] = []
        for msg in messages:
            content = msg.content
            if "STYLE EXEMPLARS" in content:
                parts = content.split("STYLE EXEMPLARS")
                head = parts[0]
                tail_parts = parts[1].split("OPTIONAL PERSONA EVIDENCE", 1)
                content = (
                    head
                    + "STYLE EXEMPLARS\n(none — privacy mode REMOTE_PROFILE_ONLY)\n\nOPTIONAL PERSONA EVIDENCE"
                    + tail_parts[1]
                    if len(tail_parts) == 2
                    else head + "STYLE EXEMPLARS\n(none — privacy mode REMOTE_PROFILE_ONLY)\n"
                )
            redacted.append(Message(role=msg.role, content=content))
        return redacted
    return messages
