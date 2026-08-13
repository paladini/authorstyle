from __future__ import annotations

import re
from typing import Protocol

from authorstyle.ingest.text_utils import split_sentences, tokenize_words, word_count
from authorstyle.models import FeatureResult


class StyleFeatureExtractor(Protocol):
    schema_version: str

    def extract(self, text: str) -> FeatureResult:
        ...


PUNCTUATION = {
    "comma": ",",
    "semicolon": ";",
    "colon": ":",
    "period": ".",
    "question": "?",
    "exclamation": "!",
    "paren_open": "(",
    "bracket_open": "[",
    "hyphen": "-",
    "em_dash": "—",
    "ellipsis": "...",
    "quote": '"',
}


class BaseStyleFeatureExtractor:
    schema_version = "1.0.0"

    def extract(self, text: str) -> FeatureResult:
        words = tokenize_words(text)
        sentences = split_sentences(text)
        paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
        wc = max(word_count(text), 1)
        sc = max(len(sentences), 1)
        pc = max(len(paragraphs), 1)

        sent_lengths = [word_count(s) for s in sentences] or [0]
        para_sent_counts = [len(split_sentences(p)) for p in paragraphs] or [0]
        para_word_counts = [word_count(p) for p in paragraphs] or [0]

        features: dict[str, float | int | dict[str, float]] = {
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "median_sentence_length": float(sorted(sent_lengths)[len(sent_lengths) // 2]),
            "median_paragraph_length_words": float(
                sorted(para_word_counts)[len(para_word_counts) // 2]
            ),
            "one_sentence_paragraph_ratio": sum(1 for c in para_sent_counts if c == 1) / pc,
            "uppercase_ratio": sum(1 for c in text if c.isupper()) / max(len(text), 1),
            "digit_ratio": sum(1 for c in text if c.isdigit()) / max(len(text), 1),
            "type_token_ratio": len(set(words)) / max(len(words), 1),
            "heading_count": len(re.findall(r"^#{1,6}\s+", text, re.MULTILINE)),
            "list_count": len(re.findall(r"^\s*[-*+]\s+", text, re.MULTILINE)),
            "blockquote_count": len(re.findall(r"^\s*>\s+", text, re.MULTILINE)),
            "code_block_count": len(re.findall(r"```", text)) // 2,
            "inline_code_count": len(re.findall(r"`[^`]+`", text)),
            "link_count": len(re.findall(r"\[[^\]]+\]\([^)]+\)", text)),
            "direct_reader_address_count": len(
                re.findall(r"\b(you|your|você|voce|seu|sua)\b", text, re.IGNORECASE)
            ),
            "rhetorical_question_count": len(re.findall(r"\?\s*$", text, re.MULTILINE)),
            "contraction_count": len(
                re.findall(r"\b\w+'\w+\b|\b(não|nao|tô|to|tá|ta)\b", text, re.IGNORECASE)
            ),
            "prose_code_ratio": (wc - len(re.findall(r"```[\s\S]*?```", text))) / wc,
        }

        for name, char in PUNCTUATION.items():
            if name == "ellipsis":
                count = text.count("...")
            else:
                count = text.count(char)
            features[f"punct_{name}_per_100_words"] = (count / wc) * 100

        pronouns = {
            "first_person": r"\b(i|me|my|we|our|eu|meu|minha|nós|nos)\b",
            "second_person": r"\b(you|your|você|voce|seu|sua)\b",
            "third_person": r"\b(he|she|they|ele|ela|eles|elas)\b",
        }
        for pname, pattern in pronouns.items():
            features[f"pronoun_{pname}_per_100_words"] = (
                len(re.findall(pattern, text, re.IGNORECASE)) / wc
            ) * 100

        short = sum(1 for sl in sent_lengths if sl <= 8)
        medium = sum(1 for sl in sent_lengths if 9 <= sl <= 20)
        long = sum(1 for sl in sent_lengths if sl > 20)
        features["sentence_length_bins"] = {
            "short_ratio": short / sc,
            "medium_ratio": medium / sc,
            "long_ratio": long / sc,
        }

        return FeatureResult(schema_version=self.schema_version, features=features)
