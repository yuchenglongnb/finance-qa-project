"""
Minimal BM25 retriever for interview-demo RAG workflow.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import jieba
try:
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover
    BM25Okapi = None


@dataclass
class RetrievedDoc:
    score: float
    doc: Dict


class BM25Retriever:
    def __init__(self, docs: List[Dict], text_fields: List[str] | None = None):
        self.docs = docs
        self.text_fields = text_fields or ["title", "content"]
        self.corpus_tokens = [self._tokenize(self._join_text(d)) for d in docs]
        self.model = BM25Okapi(self.corpus_tokens) if (self.corpus_tokens and BM25Okapi) else None

    def _join_text(self, doc: Dict) -> str:
        return " ".join(str(doc.get(field, "")).strip() for field in self.text_fields).strip()

    def _tokenize(self, text: str) -> List[str]:
        return [tok.strip() for tok in jieba.lcut(text) if tok.strip()]

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedDoc]:
        if not self.docs:
            return []
        query_tokens = self._tokenize(query)
        if self.model:
            scores = self.model.get_scores(query_tokens)
        else:
            # Fallback when rank-bm25 is not installed: token-overlap scoring.
            qset = set(query_tokens)
            scores = []
            for tokens in self.corpus_tokens:
                tset = set(tokens)
                denom = max(1, len(qset | tset))
                scores.append(len(qset & tset) / denom)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [RetrievedDoc(score=float(score), doc=self.docs[idx]) for idx, score in ranked]
