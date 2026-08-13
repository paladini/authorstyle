from __future__ import annotations

from pathlib import Path

from authorstyle.ingest.loaders import HtmlLoader, MarkdownLoader, TextLoader
from authorstyle.ingest.text_utils import (
    canonicalize_for_dedupe,
    parse_front_matter,
    sha256_text,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "corpus"


def test_markdown_loader_front_matter() -> None:
    path = FIXTURES / "en" / "article_a.md"
    loaded = MarkdownLoader().load(path)
    assert "Distributed databases overview" in loaded.raw_text
    assert loaded.metadata["mode"] == "technical"
    assert loaded.metadata["language"] == "en"


def test_text_and_html_loaders(tmp_path: Path) -> None:
    txt = tmp_path / "sample.txt"
    txt.write_text("Hello world.", encoding="utf-8")
    assert "Hello" in TextLoader().load(txt).raw_text

    html = tmp_path / "sample.html"
    html.write_text("<html><body><p>Hi</p></body></html>", encoding="utf-8")
    assert "Hi" in HtmlLoader().load(html).raw_text


def test_front_matter_parse() -> None:
    meta, body = parse_front_matter("---\ntitle: Test\n---\nBody")
    assert meta["title"] == "Test"
    assert body == "Body"


def test_canonicalize_and_sha() -> None:
    a = "Hello   world.\n\nTest."
    b = "Hello world. Test."
    assert canonicalize_for_dedupe(a) == canonicalize_for_dedupe(b)
    assert sha256_text(a) != sha256_text(canonicalize_for_dedupe(a))
