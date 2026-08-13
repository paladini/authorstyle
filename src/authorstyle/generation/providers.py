from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class Message:
    role: str
    content: str


@dataclass
class GenerationResult:
    text: str
    raw: dict[str, Any] = field(default_factory=dict)


class GenerationProvider(Protocol):
    name: str

    def generate(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        seed: int | None = None,
    ) -> GenerationResult:
        ...


class MockProvider:
    name = "mock"

    def generate(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        seed: int | None = None,
    ) -> GenerationResult:
        user_content = next((m.content for m in reversed(messages) if m.role == "user"), "")
        text = (
            "This is a mock generated response. "
            "It follows the requested task while preserving stylistic variation. "
            f"Task excerpt: {user_content[:120]}"
        )
        return GenerationResult(text=text, raw={"provider": "mock", "seed": seed})


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
    ) -> None:
        import httpx

        self.model = model
        self.client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=120.0,
        )

    def generate(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        seed: int | None = None,
    ) -> GenerationResult:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if seed is not None:
            payload["seed"] = seed
        response = self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        return GenerationResult(text=text, raw=data)


def get_provider(name: str, config: Any) -> GenerationProvider:
    if name == "mock":
        return MockProvider()
    if name in ("openai", "openai-compatible"):
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY required for openai-compatible provider")
        return OpenAICompatibleProvider(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            model=config.openai_model,
        )
    raise ValueError(f"Unknown generation provider: {name}")
