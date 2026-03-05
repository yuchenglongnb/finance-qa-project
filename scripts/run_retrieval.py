"""
Run retrieval on chunk corpus (project pipeline utility).

Usage:
  python scripts/run_retrieval.py --query "比亚迪最近公告" --top-k 5
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.hybrid_retriever import HybridRetriever


def read_jsonl(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    if not path.exists():
        return rows
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


def main():
    parser = argparse.ArgumentParser(description="Run hybrid retrieval against chunk corpus")
    parser.add_argument("--query", required=True, help="User query")
    parser.add_argument("--top-k", type=int, default=5, help="Top-K chunks")
    parser.add_argument("--processed-dir", default="data/processed", help="Processed data dir")
    args = parser.parse_args()

    chunk_path = Path(args.processed_dir) / "chunks" / "retrieval_chunks.jsonl"
    chunks = read_jsonl(chunk_path)
    if not chunks:
        print("Chunk corpus not found. Run scripts/build_retrieval_corpus.py first.")
        return

    retriever = HybridRetriever(docs=chunks, text_fields=["title", "text"], bm25_weight=0.7, overlap_weight=0.3)
    results = retriever.retrieve(query=args.query, top_k=args.top_k)

    print(f"query={args.query}")
    print(f"top_k={args.top_k}")
    print("=" * 60)
    for i, item in enumerate(results, 1):
        doc = item["doc"]
        print(f"#{i} score={item['score']:.4f} bm25={item['bm25_score']:.4f} overlap={item['overlap_score']:.4f}")
        print(f"dataset={doc.get('dataset', '')} title={doc.get('title', '')}")
        print(f"time={doc.get('publish_time') or doc.get('publish_date')}")
        print(f"url={doc.get('url', '')}")
        print("-" * 60)


if __name__ == "__main__":
    main()

