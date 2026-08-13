from __future__ import annotations

import json
import uuid
from datetime import datetime

from authorstyle.config import AppConfig
from authorstyle.embeddings.encoders import get_style_encoder
from authorstyle.generation.pipeline import GenerationPipeline
from authorstyle.generation.prompts import (
    apply_privacy_to_messages,
    build_content_plan,
    build_writer_messages,
)
from authorstyle.generation.providers import get_provider
from authorstyle.models import GenerationCandidate
from authorstyle.privacy.gate import (
    audit_messages_for_privacy,
    enforce_privacy_provider,
)
from authorstyle.scoring.metrics import (
    aggregate_score,
    calibration_percentile,
    score_content_adherence,
    score_explicit_style,
    score_naturalness,
    score_originality,
    score_style_embedding,
)
from authorstyle.storage import ProfileStore

BASELINES = ("generic", "card", "examples", "hybrid", "full")


class EvaluationService:
    def __init__(self, profile_id: str, config: AppConfig | None = None) -> None:
        self.store = ProfileStore(profile_id)
        self.config = config or AppConfig.from_env()

    def run(self) -> dict:
        documents = self.store.sqlite.list_documents(self.store.profile_id)
        profiles = self.store.sqlite.list_profiles(self.store.profile_id)
        global_profile = next((p for p in profiles if p.scope.value == "global"), None)
        if not global_profile:
            raise ValueError("No profile found. Run 'authorstyle analyze' first.")

        test_docs = [d for d in documents if d.split == "test"]
        chunks = self.store.sqlite.list_chunks_for_profile(self.store.profile_id)
        test_chunks = [c for c in chunks if any(d.id == c.document_id for d in test_docs)]
        train_chunks = [c for c in chunks if any(d.id == c.document_id and d.split == "train" for d in documents)]

        style_encoder = get_style_encoder(self.config.style_encoder)
        genuine_distances = []
        centroid = global_profile.style_embedding_centroid
        if centroid:
            import numpy as np

            c = np.asarray(centroid)
            for chunk in test_chunks:
                vec = style_encoder.encode([chunk.text])[0]
                genuine_distances.append(float(np.linalg.norm(vec - c)))

        provider = enforce_privacy_provider(
            self.config.privacy_mode,
            get_provider(self.config.generation_provider, self.config),
        )
        pipeline = GenerationPipeline(self.store, self.config)

        results = {
            "profile_id": self.store.profile_id,
            "timestamp": datetime.utcnow().isoformat(),
            "test_documents": len({d.canonical_document_id for d in test_docs}),
            "baselines": {},
            "limitations": [
                "Style and topic can remain entangled; review source/mode metadata.",
                "Percentiles are relative to held-out genuine author documents only.",
            ],
        }

        for baseline in BASELINES:
            if not test_docs:
                break
            prompt = f"Rewrite this topic faithfully: {test_docs[0].title or 'untitled'}"
            if baseline == "full":
                run = pipeline.run(prompt)
                candidate = run.candidates[run.selected_candidate_index or 0]
            else:
                content_plan = build_content_plan(prompt)
                exemplars = []
                style_card = None
                if baseline in ("card", "hybrid", "full"):
                    style_card = global_profile.style_card
                if baseline in ("examples", "hybrid"):
                    exemplars = [train_chunks[0].text] if train_chunks else []
                messages = build_writer_messages(
                    prompt, content_plan, style_card, exemplars, None
                )
                messages = apply_privacy_to_messages(messages, self.config.privacy_mode)
                audit_messages_for_privacy(messages, self.config.privacy_mode, exemplars)
                result = provider.generate(messages, seed=7)
                style_vec = style_encoder.encode([result.text])[0]
                explicit_score, diagnostics = score_explicit_style(result.text, global_profile)
                orig_score, _ = score_originality(
                    result.text, [c.text for c in chunks], self.config.originality
                )
                candidate = GenerationCandidate(
                    text=result.text,
                    style_embedding_score=score_style_embedding(style_vec, global_profile),
                    explicit_style_score=explicit_score,
                    content_score=score_content_adherence(result.text, content_plan),
                    naturalness_score=score_naturalness(result.text),
                    originality_score=orig_score,
                    diagnostics=diagnostics,
                )
                candidate.aggregate_score = aggregate_score(candidate, self.config.scoring_weights)

            import numpy as np

            cand_dist = None
            percentile = None
            if centroid:
                vec = style_encoder.encode([candidate.text])[0]
                cand_dist = float(np.linalg.norm(vec - np.asarray(centroid)))
                percentile = calibration_percentile(cand_dist, genuine_distances)

            results["baselines"][baseline] = {
                "aggregate_score": candidate.aggregate_score,
                "style_embedding_score": candidate.style_embedding_score,
                "explicit_style_score": candidate.explicit_style_score,
                "content_score": candidate.content_score,
                "naturalness_score": candidate.naturalness_score,
                "originality_score": candidate.originality_score,
                "style_distance": cand_dist,
                "held_out_percentile": percentile,
                "diagnostics": candidate.diagnostics,
            }

        eval_id = str(uuid.uuid4())
        json_path = self.store.evaluations_dir() / f"{eval_id}.json"
        md_path = self.store.evaluations_dir() / f"{eval_id}.md"
        json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        md_lines = [
            f"# Evaluation — {self.store.profile_id}",
            "",
            f"Test documents: {results['test_documents']}",
            "",
        ]
        for name, metrics in results["baselines"].items():
            md_lines.append(f"## Baseline: {name}")
            for key, value in metrics.items():
                if key != "diagnostics":
                    md_lines.append(f"- {key}: {value}")
            md_lines.append("")
        md_path.write_text("\n".join(md_lines), encoding="utf-8")
        results["evaluation_id"] = eval_id
        results["paths"] = {"json": str(json_path), "md": str(md_path)}
        return results
