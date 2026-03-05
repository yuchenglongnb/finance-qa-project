"""
Diagnose announcement data availability for downstream extraction/retrieval.

Usage:
  python scripts/diagnose_announcement_data.py
  python scripts/diagnose_announcement_data.py --data-file data/processed/announcements/announcements_cleaned.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


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


def pct(n: int, d: int) -> str:
    return f"{(n / d * 100):.2f}%" if d else "0.00%"


def main():
    parser = argparse.ArgumentParser(description="Diagnose announcement data quality and enrichability")
    parser.add_argument(
        "--data-file",
        default="data/processed/announcements/announcements_cleaned.jsonl",
        help="Announcement processed file",
    )
    args = parser.parse_args()

    path = Path(args.data_file)
    rows = read_jsonl(path)
    total = len(rows)

    content_nonempty = sum(1 for r in rows if str(r.get("content", "")).strip())
    url_nonempty = sum(1 for r in rows if str(r.get("url", "")).strip())
    pdf_nonempty = sum(1 for r in rows if str(r.get("pdf_url", "")).strip())
    enrichable = sum(
        1
        for r in rows
        if (not str(r.get("content", "")).strip())
        and (str(r.get("url", "")).strip() or str(r.get("pdf_url", "")).strip())
    )

    print(f"file={path}")
    print(f"total={total}")
    print(f"content_nonempty={content_nonempty} ({pct(content_nonempty, total)})")
    print(f"url_nonempty={url_nonempty} ({pct(url_nonempty, total)})")
    print(f"pdf_url_nonempty={pdf_nonempty} ({pct(pdf_nonempty, total)})")
    print(f"enrichable_empty_rows={enrichable} ({pct(enrichable, total)})")

    if enrichable == 0:
        print("diagnosis=no link-bearing empty rows; content enrichment cannot improve with current source fields")
    else:
        print("diagnosis=enrichment likely beneficial; run enrich_announcement_content.py")


if __name__ == "__main__":
    main()

