"""
Minimal data quality check for collected JSONL files.

Usage:
  python scripts/verify_data_quality.py
  python scripts/verify_data_quality.py --sample-size 100 --data-dir data/raw
"""
import argparse
import json
from pathlib import Path
from typing import Dict, List


def load_jsonl(path: Path) -> List[Dict]:
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


def latest_jsonl(dir_path: Path) -> Path | None:
    files = sorted(dir_path.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def coverage_report(rows: List[Dict], required_fields: List[str], sample_size: int) -> Dict:
    sampled = rows[:sample_size]
    total = len(sampled)
    if total == 0:
        return {"sampled": 0, "valid": 0, "valid_rate": 0.0, "field_coverage": {}}

    valid = 0
    field_coverage: Dict[str, float] = {}

    for field in required_fields:
        present = sum(1 for row in sampled if row.get(field))
        field_coverage[field] = round(present / total, 4)

    for row in sampled:
        if all(row.get(field) for field in required_fields):
            valid += 1

    return {
        "sampled": total,
        "valid": valid,
        "valid_rate": round(valid / total, 4),
        "field_coverage": field_coverage,
    }


def print_section(name: str, report: Dict, file_path: Path | None):
    print("=" * 60)
    print(f"[{name}]")
    print(f"file: {file_path if file_path else 'N/A'}")
    print(f"sampled: {report['sampled']}")
    print(f"valid: {report['valid']}")
    print(f"valid_rate: {report['valid_rate']:.2%}" if report["sampled"] else "valid_rate: N/A")
    print("field_coverage:")
    for k, v in report["field_coverage"].items():
        print(f"  - {k}: {v:.2%}")


def main():
    parser = argparse.ArgumentParser(description="Verify minimal JSONL data quality")
    parser.add_argument("--data-dir", default="data/raw", help="Raw data root dir")
    parser.add_argument("--sample-size", type=int, default=100, help="Rows per dataset to inspect")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    news_file = latest_jsonl(data_dir / "news")
    ann_file = latest_jsonl(data_dir / "announcements")

    news_rows = load_jsonl(news_file) if news_file else []
    ann_rows = load_jsonl(ann_file) if ann_file else []

    news_required = ["title", "publish_time", "content", "url"]
    ann_required = ["title", "stock_code", "publish_date"]

    news_report = coverage_report(news_rows, news_required, args.sample_size)
    ann_report = coverage_report(ann_rows, ann_required, args.sample_size)

    print_section("News", news_report, news_file)
    print_section("Announcements", ann_report, ann_file)
    print("=" * 60)


if __name__ == "__main__":
    main()
