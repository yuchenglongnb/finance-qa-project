"""
Chunking utilities for long Chinese financial text.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ChunkConfig:
    chunk_size: int = 400
    chunk_overlap: int = 50
    min_chunk_len: int = 30


def _normalize_text(text: str) -> str:
    return " ".join(str(text).replace("\u3000", " ").split())


def split_text(text: str, config: ChunkConfig) -> List[str]:
    text = _normalize_text(text)
    if len(text) <= config.chunk_size:
        return [text] if len(text) >= config.min_chunk_len else []

    chunks: List[str] = []
    step = max(1, config.chunk_size - config.chunk_overlap)
    for start in range(0, len(text), step):
        chunk = text[start : start + config.chunk_size].strip()
        if len(chunk) >= config.min_chunk_len:
            chunks.append(chunk)
        if start + config.chunk_size >= len(text):
            break
    return chunks


def build_chunks_from_doc(doc: Dict, dataset: str, config: ChunkConfig) -> List[Dict]:
    title = str(doc.get("title", "")).strip()
    content = str(doc.get("content", "")).strip()
    if not content:
        # Announcements often do not provide正文 in source API; keep title-only chunk.
        content = title
    if not content:
        return []

    text = f"{title}\n{content}" if title else content
    text_chunks = split_text(text, config)
    if not text_chunks and dataset == "announcements" and len(text) >= 8:
        text_chunks = [text]
    results: List[Dict] = []
    for idx, chunk in enumerate(text_chunks):
        results.append(
            {
                "chunk_id": f"{doc.get('id', 'unknown')}_{idx}",
                "doc_id": doc.get("id", ""),
                "dataset": dataset,
                "chunk_index": idx,
                "text": chunk,
                "title": title,
                "publish_time": doc.get("publish_time", ""),
                "publish_date": doc.get("publish_date", ""),
                "source": doc.get("source", ""),
                "stock_code": doc.get("stock_code", ""),
                "stock_name": doc.get("stock_name", ""),
                "announcement_type": doc.get("announcement_type", ""),
                "url": doc.get("url", ""),
            }
        )
    return results
