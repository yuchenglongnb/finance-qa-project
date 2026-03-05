"""
Enrich announcement content by fetching PDF/HTML when content is empty.

Usage:
  python scripts/enrich_announcement_content.py
  python scripts/enrich_announcement_content.py --max-items 500 --timeout 20 --retries 2
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict, List

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_processing.announcement_content_extractor import (
    extract_text_from_html_bytes,
    extract_text_from_pdf_bytes,
    fetch_bytes,
)


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


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def try_fetch_and_extract(
    row: Dict, timeout: int, retries: int, max_chars: int, max_pages: int
) -> tuple[str, str]:
    pdf_url = str(row.get("pdf_url", "")).strip()
    url = str(row.get("url", "")).strip()

    if pdf_url:
        for _ in range(retries + 1):
            data = fetch_bytes(pdf_url, timeout=timeout)
            text = extract_text_from_pdf_bytes(data or b"", max_chars=max_chars, max_pages=max_pages)
            if text:
                return text, "pdf_url"
            time.sleep(0.3)

    if url:
        for _ in range(retries + 1):
            data = fetch_bytes(url, timeout=timeout)
            if data:
                # Try PDF first (some URLs point directly to pdf)
                text = extract_text_from_pdf_bytes(data, max_chars=max_chars, max_pages=max_pages)
                if not text:
                    text = extract_text_from_html_bytes(data, max_chars=max_chars)
                if text:
                    return text, "url"
            time.sleep(0.3)

    return "", ""


def main():
    parser = argparse.ArgumentParser(description="Enrich announcement content by fetching URL/PDF")
    parser.add_argument("--processed-dir", default="data/processed", help="Processed data directory")
    parser.add_argument("--input-file", default="announcements_cleaned.jsonl", help="Input file name")
    parser.add_argument(
        "--output-file",
        default="announcements_enriched.jsonl",
        help="Output file name",
    )
    parser.add_argument("--max-items", type=int, default=1000, help="Max empty-content rows to try")
    parser.add_argument("--timeout", type=int, default=20, help="Request timeout seconds")
    parser.add_argument("--retries", type=int, default=1, help="Retries per URL")
    parser.add_argument("--max-chars", type=int, default=8000, help="Max extracted content length")
    parser.add_argument("--max-pages", type=int, default=8, help="Max PDF pages to parse")
    parser.add_argument("--save-every", type=int, default=50, help="Checkpoint save interval")
    args = parser.parse_args()

    base = Path(args.processed_dir) / "announcements"
    in_path = base / args.input_file
    out_path = base / args.output_file
    report_path = base / "announcements_enrich_report.json"

    rows = read_jsonl(in_path)
    if not rows:
        print(f"No data found: {in_path}")
        return

    tried = 0
    success = 0
    source_pdf = 0
    source_url = 0
    eligible_with_link = 0

    try:
        for row in rows:
            content = str(row.get("content", "")).strip()
            if content:
                continue
            if tried >= args.max_items:
                break
            if str(row.get("pdf_url", "")).strip() or str(row.get("url", "")).strip():
                eligible_with_link += 1

            text, source = try_fetch_and_extract(
                row=row,
                timeout=args.timeout,
                retries=args.retries,
                max_chars=args.max_chars,
                max_pages=args.max_pages,
            )
            tried += 1
            if text:
                row["content"] = text
                row["content_source"] = source
                success += 1
                if source == "pdf_url":
                    source_pdf += 1
                elif source == "url":
                    source_url += 1

            if tried % max(1, args.save_every) == 0:
                write_jsonl(out_path, rows)
    except KeyboardInterrupt:
        print("Interrupted by user. Writing checkpoint output...")

    write_jsonl(out_path, rows)

    filled_lengths = [len(str(r.get("content", ""))) for r in rows if r.get("content_source")]

    report = {
        "input_file": str(in_path),
        "output_file": str(out_path),
        "total_rows": len(rows),
        "tried_empty_content_rows": tried,
        "eligible_with_link": eligible_with_link,
        "success_filled": success,
        "success_rate": round(success / tried, 4) if tried else 0.0,
        "source_pdf_url": source_pdf,
        "source_url": source_url,
        "content_len_avg": round(sum(filled_lengths) / len(filled_lengths), 1) if filled_lengths else 0,
        "content_len_min": min(filled_lengths) if filled_lengths else 0,
        "content_len_max": max(filled_lengths) if filled_lengths else 0,
        "content_len_p50": sorted(filled_lengths)[len(filled_lengths) // 2] if filled_lengths else 0,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("Announcement content enrichment finished.")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
