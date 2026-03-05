"""
Build chunk-level retrieval corpus from cleaned documents.

Usage:
  python scripts/build_retrieval_corpus.py
  python scripts/build_retrieval_corpus.py --processed-dir data/processed --chunk-size 400 --chunk-overlap 50
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_processing.text_splitter import ChunkConfig, build_chunks_from_doc


def read_jsonl(path: Path) -> Iterable[Dict]:
    if not path.exists():
        return []
    rows: List[Dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Build retrieval corpus chunks from processed data")
    parser.add_argument("--processed-dir", default="data/processed", help="Processed data directory")
    parser.add_argument("--chunk-size", type=int, default=400, help="Chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=50, help="Chunk overlap")
    parser.add_argument("--min-chunk-len", type=int, default=30, help="Min chunk length")
    args = parser.parse_args()

    processed = Path(args.processed_dir)
    news_path = processed / "news" / "news_cleaned.jsonl"
    ann_path = processed / "announcements" / "announcements_cleaned.jsonl"

    news_docs = list(read_jsonl(news_path))
    ann_docs = list(read_jsonl(ann_path))

    cfg = ChunkConfig(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        min_chunk_len=args.min_chunk_len,
    )

    all_chunks: List[Dict] = []
    for doc in news_docs:
        all_chunks.extend(build_chunks_from_doc(doc, dataset="news", config=cfg))
    for doc in ann_docs:
        all_chunks.extend(build_chunks_from_doc(doc, dataset="announcements", config=cfg))

    out_path = processed / "chunks" / "retrieval_chunks.jsonl"
    write_jsonl(out_path, all_chunks)

    print("Build retrieval corpus finished.")
    print(f"news_docs={len(news_docs)}")
    print(f"announcement_docs={len(ann_docs)}")
    print(f"total_chunks={len(all_chunks)}")
    print(f"output={out_path}")


if __name__ == "__main__":
    main()

