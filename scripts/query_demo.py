"""
Local retrieval demo for interview presentation.

Usage:
  python scripts/query_demo.py --query "比亚迪最近有什么公告？" --top-k 5
  python scripts/query_demo.py --query "新能源汽车政策" --dataset news --top-k 3
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.bm25_retriever import BM25Retriever


def load_jsonl(path: Path) -> List[Dict]:
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


def format_doc(dataset: str, doc: Dict, score: float) -> str:
    if dataset == "announcements":
        return (
            f"score={score:.4f}\n"
            f"title={doc.get('title', '')}\n"
            f"stock_code={doc.get('stock_code', '')}\n"
            f"publish_date={doc.get('publish_date', '')}\n"
            f"url={doc.get('url', '')}\n"
        )
    return (
        f"score={score:.4f}\n"
        f"title={doc.get('title', '')}\n"
        f"publish_time={doc.get('publish_time', '')}\n"
        f"source={doc.get('source', '')}\n"
        f"url={doc.get('url', '')}\n"
    )


def main():
    parser = argparse.ArgumentParser(description="Minimal BM25 retrieval demo")
    parser.add_argument("--query", required=True, help="User query")
    parser.add_argument("--top-k", type=int, default=5, help="Top K docs")
    parser.add_argument(
        "--dataset",
        choices=["all", "news", "announcements"],
        default="all",
        help="Dataset selection",
    )
    parser.add_argument("--processed-dir", default="data/processed", help="Processed data dir")
    args = parser.parse_args()

    processed = Path(args.processed_dir)
    news_docs = load_jsonl(processed / "news" / "news_cleaned.jsonl")
    ann_docs = load_jsonl(processed / "announcements" / "announcements_cleaned.jsonl")

    targets = []
    if args.dataset in ["all", "news"]:
        targets.append(("news", news_docs, ["title", "content", "summary"]))
    if args.dataset in ["all", "announcements"]:
        targets.append(("announcements", ann_docs, ["title", "content", "announcement_type", "stock_name"]))

    if not any(docs for _, docs, _ in targets):
        print("No processed data found. Run clean_and_prepare_data.py first.")
        return

    print(f"Query: {args.query}")
    print("=" * 60)
    for name, docs, fields in targets:
        if not docs:
            print(f"[{name}] no data")
            print("-" * 60)
            continue
        retriever = BM25Retriever(docs=docs, text_fields=fields)
        results = retriever.retrieve(args.query, top_k=args.top_k)
        print(f"[{name}] total_docs={len(docs)}")
        for idx, item in enumerate(results, 1):
            print(f"#{idx}")
            print(format_doc(name, item.doc, item.score))
        print("-" * 60)


if __name__ == "__main__":
    main()

