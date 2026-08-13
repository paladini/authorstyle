from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

import yaml


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_unicode(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def canonicalize_for_dedupe(text: str) -> str:
    text = normalize_unicode(text)
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}, text
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    body = text[match.end() :]
    return meta, body


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def tokenize_words(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower(), flags=re.UNICODE)


def load_ignore_patterns(root: Path) -> list[str]:
    ignore_file = root / ".authorstyleignore"
    if not ignore_file.exists():
        return []
    patterns: list[str] = []
    for line in ignore_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(line)
    return patterns


def should_ignore(path: Path, patterns: list[str]) -> bool:
    rel = path.as_posix()
    for pattern in patterns:
        if pattern.endswith("/") and rel.startswith(pattern.rstrip("/")):
            return True
        if pattern.startswith("*") and rel.endswith(pattern[1:]):
            return True
        if pattern in rel.split("/"):
            return True
    return False
