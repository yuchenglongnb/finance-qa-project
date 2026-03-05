"""
Hybrid retriever: BM25 + IDF-weighted overlap + entity boost.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List, Tuple

import jieba

from src.retrieval.bm25_retriever import BM25Retriever


# Improve Chinese entity tokenization.
_ENTITY_WORDS = [
    "比亚迪",
    "宁德时代",
    "贵州茅台",
    "中国平安",
    "招商银行",
    "工商银行",
    "建设银行",
    "中国银行",
    "农业银行",
    "中国石化",
    "中国石油",
    "中国移动",
    "中国联通",
    "中国电信",
    "美的集团",
    "格力电器",
    "海尔智家",
    "长城汽车",
    "吉利汽车",
    "上汽集团",
    "东方雨虹",
    "万科",
    "保利发展",
]
for _w in _ENTITY_WORDS:
    jieba.add_word(_w, freq=50000)


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
        self.generic_titles = {"h股公告", "h股", "公告", "pdf"}
        self._idf = self._build_idf(self.doc_tokens)

    def _join_text(self, doc: Dict) -> str:
        return " ".join(str(doc.get(f, "")).strip() for f in self.text_fields).strip()

    def _build_idf(self, doc_token_lists: List[List[str]]) -> Dict[str, float]:
        n = max(1, len(doc_token_lists))
        df: Counter = Counter()
        for tokens in doc_token_lists:
            for t in set(tokens):
                df[t] += 1
        return {t: math.log((n + 1) / (cnt + 1)) + 1.0 for t, cnt in df.items()}

    def _idf_val(self, token: str) -> float:
        return self._idf.get(token, math.log(2) + 1.0)

    def _overlap_score(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        if not query_tokens or not doc_tokens:
            return 0.0
        q = set(query_tokens)
        d = set(doc_tokens)
        inter = q & d
        denom = sum(self._idf_val(t) for t in q)
        if denom <= 0:
            return 0.0
        return sum(self._idf_val(t) for t in inter) / denom

    def _entity_boost_score(self, query: str, query_tokens: List[str], doc: Dict) -> float:
        title = str(doc.get("title", "")).strip().lower()
        stock_name = str(doc.get("stock_name", "")).strip().lower()
        stock_code = str(doc.get("stock_code", "")).strip().lower()
        q = query.strip().lower()

        score = 0.0
        if stock_name and stock_name in q:
            score += 0.6
        if stock_code and stock_code in q:
            score += 0.7

        valid_tokens = [t.lower() for t in query_tokens if len(t) >= 2]
        hit = sum(1 for t in valid_tokens if t in title or (stock_name and t in stock_name))
        if valid_tokens:
            score += 0.4 * (hit / len(valid_tokens))

        if title in self.generic_titles:
            score -= 0.2

        return max(-0.5, min(1.2, score))

    def _select_candidates_by_entity(self, query: str) -> Tuple[List[Dict], Dict]:
        q = query.strip().lower()
        code_hits = set(re.findall(r"\b\d{6}\b", q))
        name_hits = set()
        for d in self.docs:
            name = str(d.get("stock_name", "")).strip().lower()
            if name and name in q:
                name_hits.add(name)

        if not code_hits and not name_hits:
            return self.docs, {"applied": False, "hits": 0}

        subset = []
        for d in self.docs:
            code = str(d.get("stock_code", "")).strip().lower()
            name = str(d.get("stock_name", "")).strip().lower()
            if (code and code in code_hits) or (name and name in name_hits):
                subset.append(d)

        if subset:
            return subset, {"applied": True, "hits": len(subset)}
        return self.docs, {"applied": False, "hits": 0}

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        if not self.docs:
            return []

        candidate_docs, entity_meta = self._select_candidates_by_entity(query)

        bm25 = BM25Retriever(docs=candidate_docs, text_fields=self.text_fields)
        bm25_results = bm25.retrieve(query=query, top_k=len(candidate_docs))
        bm25_map = {item.doc.get("chunk_id", str(i)): item.score for i, item in enumerate(bm25_results)}

        query_tokens = _tokenize(query)
        merged: List[Dict] = []
        for idx, doc in enumerate(candidate_docs):
            key = doc.get("chunk_id", f"c{idx}")
            bm25_score = float(bm25_map.get(key, 0.0))
            overlap_score = self._overlap_score(query_tokens, _tokenize(self._join_text(doc)))
            entity_boost = self._entity_boost_score(query, query_tokens, doc)
            score = self.bm25_weight * bm25_score + self.overlap_weight * overlap_score + 0.4 * entity_boost
            merged.append(
                {
                    "score": score,
                    "bm25_score": bm25_score,
                    "overlap_score": overlap_score,
                    "entity_boost": entity_boost,
                    "entity_filter_applied": entity_meta["applied"],
                    "entity_filter_hits": entity_meta["hits"],
                    "doc": doc,
                }
            )

        merged.sort(key=lambda x: x["score"], reverse=True)
        return merged[:top_k]

