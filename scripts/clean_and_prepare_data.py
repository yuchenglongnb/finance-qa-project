"""
Clean, deduplicate and normalize raw JSONL data for downstream indexing.

Usage:
  python scripts/clean_and_prepare_data.py
  python scripts/clean_and_prepare_data.py --data-dir data/raw --output-dir data/processed --min-content-len 20
"""
import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def read_jsonl(path: Path) -> Iterable[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def stable_id(parts: List[str]) -> str:
    content = "||".join(parts)
    return hashlib.sha1(content.encode("utf-8")).hexdigest()


def normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def clean_news(rows: Iterable[Dict], min_content_len: int) -> Tuple[List[Dict], Dict]:
    cleaned: List[Dict] = []
    seen = set()
    total = 0
    dropped_empty = 0
    dropped_short = 0
    dropped_dup = 0

    for row in rows:
        total += 1
        title = normalize_text(row.get("title"))
        content = normalize_text(row.get("content"))
        publish_time = normalize_text(row.get("publish_time"))
        url = normalize_text(row.get("url"))
        source = normalize_text(row.get("source"))

        if not title or not content or not publish_time:
            dropped_empty += 1
            continue
        if len(content) < min_content_len:
            dropped_short += 1
            continue

        doc_id = stable_id([title, publish_time, url, source])
        if doc_id in seen:
            dropped_dup += 1
            continue
        seen.add(doc_id)

        cleaned.append(
            {
                "id": doc_id,
                "title": title,
                "content": content,
                "summary": normalize_text(row.get("summary")) or content[:200],
                "publish_time": publish_time,
                "source": source,
                "url": url,
                "category": normalize_text(row.get("category")) or "综合",
                "keywords": row.get("keywords", []),
                "crawl_time": normalize_text(row.get("crawl_time")),
            }
        )

    stats = {
        "total": total,
        "kept": len(cleaned),
        "dropped_empty": dropped_empty,
        "dropped_short": dropped_short,
        "dropped_dup": dropped_dup,
    }
    return cleaned, stats


def clean_announcements(rows: Iterable[Dict], min_content_len: int) -> Tuple[List[Dict], Dict]:
    cleaned: List[Dict] = []
    seen = set()
    total = 0
    dropped_empty = 0
    dropped_short = 0
    dropped_dup = 0

    for row in rows:
        total += 1
        title = normalize_text(row.get("title"))
        stock_code = normalize_text(row.get("stock_code"))
        publish_date = normalize_text(row.get("publish_date"))
        content = normalize_text(row.get("content"))

        if not title or not stock_code or not publish_date:
            dropped_empty += 1
            continue
        if content and len(content) < min_content_len:
            dropped_short += 1
            continue

        doc_id = stable_id([title, stock_code, publish_date, normalize_text(row.get("url"))])
        if doc_id in seen:
            dropped_dup += 1
            continue
        seen.add(doc_id)

        cleaned.append(
            {
                "id": doc_id,
                "title": title,
                "stock_code": stock_code,
                "stock_name": normalize_text(row.get("stock_name")),
                "announcement_type": normalize_text(row.get("announcement_type")) or "其他",
                "publish_date": publish_date,
                "content": content,
                "url": normalize_text(row.get("url")),
                "pdf_url": normalize_text(row.get("pdf_url")),
                "crawl_time": normalize_text(row.get("crawl_time")),
            }
        )

    stats = {
        "total": total,
        "kept": len(cleaned),
        "dropped_empty": dropped_empty,
        "dropped_short": dropped_short,
        "dropped_dup": dropped_dup,
    }
    return cleaned, stats


def latest_file(dir_path: Path) -> Path | None:
    files = sorted(dir_path.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def main():
    parser = argparse.ArgumentParser(description="Clean and prepare raw financial QA data")
    parser.add_argument("--data-dir", default="data/raw", help="Raw data directory")
    parser.add_argument("--output-dir", default="data/processed", help="Processed data directory")
    parser.add_argument("--min-content-len", type=int, default=20, help="Minimum content length")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)

    news_src = latest_file(data_dir / "news")
    ann_src = latest_file(data_dir / "announcements")

    if not news_src and not ann_src:
        print("No raw JSONL files found. Run collection first.")
        return

    if news_src:
        news_clean, news_stats = clean_news(read_jsonl(news_src), args.min_content_len)
        news_out = output_dir / "news" / "news_cleaned.jsonl"
        write_jsonl(news_out, news_clean)
        print("[News]")
        print(f"src: {news_src}")
        print(f"out: {news_out}")
        print(news_stats)

    if ann_src:
        ann_clean, ann_stats = clean_announcements(read_jsonl(ann_src), args.min_content_len)
        ann_out = output_dir / "announcements" / "announcements_cleaned.jsonl"
        write_jsonl(ann_out, ann_clean)
        print("[Announcements]")
        print(f"src: {ann_src}")
        print(f"out: {ann_out}")
        print(ann_stats)


if __name__ == "__main__":
    main()
