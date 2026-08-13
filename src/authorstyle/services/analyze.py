from __future__ import annotations

import hashlib
import json

from authorstyle.config import AppConfig
from authorstyle.embeddings.encoders import get_semantic_encoder, get_style_encoder
from authorstyle.embeddings.service import EmbeddingService
from authorstyle.evaluation.split import assign_splits, validate_split_isolation
from authorstyle.ingest.pipeline import ingest_corpus
from authorstyle.models import ProfileScope
from authorstyle.profile.builder import (
    build_profile,
    select_exemplars,
    style_card_to_markdown,
)
from authorstyle.storage import ProfileStore
from authorstyle.stylometry.base import BaseStyleFeatureExtractor


def corpus_hash(documents: list) -> str:
    payload = sorted((d.canonical_document_id, d.sha256) for d in documents)
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()


class AnalyzeService:
    def __init__(self, profile_id: str, config: AppConfig | None = None) -> None:
        self.store = ProfileStore(profile_id)
        self.config = config or AppConfig.from_env()
        self.extractor = BaseStyleFeatureExtractor()
        self.embedding_service = EmbeddingService(self.store.embeddings)

    def ingest(self, corpus_dir) -> None:
        documents, chunks = ingest_corpus(
            self.store.profile_id,
            corpus_dir,
            self.config.chunk,
        )
        documents = assign_splits(
            documents,
            self.config.split.train_ratio,
            self.config.split.validation_ratio,
            self.config.split.test_ratio,
            self.config.split.seed,
        )
        validate_split_isolation(documents)
        for doc in documents:
            self.store.sqlite.upsert_document(doc)
        for chunk in chunks:
            features = self.extractor.extract(chunk.text)
            chunk.style_features = features.features
            self.store.sqlite.upsert_chunk(chunk)
        self.store.sqlite.set_meta("corpus_hash", corpus_hash(documents))

    def analyze(self) -> None:
        documents = self.store.sqlite.list_documents(self.store.profile_id)
        if not documents:
            raise ValueError("No documents ingested. Run 'authorstyle ingest' first.")
        chunks = self.store.sqlite.list_chunks_for_profile(self.store.profile_id)
        train_docs = [d for d in documents if (d.split or "train") == "train"]
        train_doc_ids = {d.id for d in train_docs}
        train_chunks = [c for c in chunks if c.document_id in train_doc_ids]
        if not train_chunks:
            raise ValueError(
                "No training documents available after split. Ingest more corpus material."
            )

        style_encoder = get_style_encoder(self.config.style_encoder)
        semantic_encoder = get_semantic_encoder(self.config.semantic_encoder)
        style_vectors, style_refs = self.embedding_service.encode_style(
            style_encoder, [c.text for c in train_chunks]
        )
        semantic_vectors, sem_refs = self.embedding_service.encode_semantic(
            semantic_encoder, [c.text for c in train_chunks]
        )
        for chunk, sref, mref in zip(train_chunks, style_refs, sem_refs, strict=True):
            chunk.style_embedding_ref = sref
            chunk.semantic_embedding_ref = mref
            self.store.sqlite.upsert_chunk(chunk)

        c_hash = self.store.sqlite.get_meta("corpus_hash") or corpus_hash(documents)
        global_profile = build_profile(
            self.store.profile_id,
            ProfileScope.GLOBAL,
            None,
            train_docs,
            train_chunks,
            style_vectors,
            c_hash,
            self.config.mode_evidence,
        )
        if style_vectors.size:
            centroid = style_vectors.mean(axis=0)
            exemplars = select_exemplars(
                train_chunks,
                train_docs,
                style_vectors,
                semantic_vectors,
                centroid,
            )
            global_profile.prototype_chunk_ids = [e.chunk_id for e in exemplars]
            if global_profile.style_card:
                for section in global_profile.style_card.sections.values():
                    section.evidence_chunk_ids = global_profile.prototype_chunk_ids[:2]

        self.store.sqlite.upsert_profile(global_profile)
        if global_profile.style_card:
            self.store.style_card_json_path().write_text(
                global_profile.style_card.model_dump_json(indent=2),
                encoding="utf-8",
            )
            self.store.style_card_md_path().write_text(
                style_card_to_markdown(global_profile.style_card),
                encoding="utf-8",
            )

        modes = sorted({d.mode for d in train_docs if d.mode})
        for mode in modes:
            mode_docs = [d for d in train_docs if d.mode == mode]
            mode_chunks = [c for c in train_chunks if c.document_id in {d.id for d in mode_docs}]
            if not mode_chunks:
                continue
            mv, _ = self.embedding_service.encode_style(style_encoder, [c.text for c in mode_chunks])
            sv, _ = self.embedding_service.encode_semantic(
                semantic_encoder, [c.text for c in mode_chunks]
            )
            profile = build_profile(
                self.store.profile_id,
                ProfileScope.MODE,
                mode,
                mode_docs,
                mode_chunks,
                mv,
                c_hash,
                self.config.mode_evidence,
            )
            if mv.size:
                centroid = mv.mean(axis=0)
                exemplars = select_exemplars(
                    mode_chunks, mode_docs, mv, sv, centroid, mode=mode
                )
                profile.prototype_chunk_ids = [e.chunk_id for e in exemplars]
            self.store.sqlite.upsert_profile(profile)
