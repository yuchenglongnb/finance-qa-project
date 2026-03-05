"""
Hybrid retriever: BM25 score + token-overlap score.
"""
from __future__ import annotations

from typing import Dict, List

import jieba

from src.retrieval.bm25_retriever import BM25Retriever


def _tokenize(text: str) -> List[str]:
    return [w.strip() for w in jieba.lcut(text) if w.strip()]


class HybridRetriever:
    def __init__(
        self,
        docs: List[Dict],
        text_fields: List[str] | None = None,
        bm25_weight: float = 0.7,
        overlap_weight: float = 0.3,
    ):
        self.docs = docs
        self.text_fields = text_fields or ["title", "text"]
        self.bm25_weight = bm25_weight
        self.overlap_weight = overlap_weight
        self.bm25 = BM25Retriever(docs=docs, text_fields=self.text_fields)
        self.doc_tokens = [_tokenize(self._join_text(doc)) for doc in docs]

    def _join_text(self, doc: Dict) -> str:
        return " ".join(str(doc.get(f, "")).strip() for f in self.text_fields).strip()

    def _overlap_score(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        if not query_tokens or not doc_tokens:
            return 0.0
        q = set(query_tokens)
        d = set(doc_tokens)
        return len(q & d) / max(1, len(q))

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        if not self.docs:
            return []

        bm25_results = self.bm25.retrieve(query=query, top_k=len(self.docs))
        bm25_map = {item.doc.get("chunk_id", str(i)): item.score for i, item in enumerate(bm25_results)}

        query_tokens = _tokenize(query)
        merged: List[Dict] = []
        for idx, doc in enumerate(self.docs):
            key = doc.get("chunk_id", str(idx))
            bm25_score = float(bm25_map.get(key, 0.0))
            overlap_score = self._overlap_score(query_tokens, self.doc_tokens[idx])
            score = self.bm25_weight * bm25_score + self.overlap_weight * overlap_score
            merged.append(
                {
                    "score": score,
                    "bm25_score": bm25_score,
                    "overlap_score": overlap_score,
                    "doc": doc,
                }
            )

        merged.sort(key=lambda x: x["score"], reverse=True)
        return merged[:top_k]

