"""
Company announcement crawler with AKShare + cninfo fallback.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import akshare as ak
import requests
from loguru import logger

from .base_crawler import BaseCrawler


class AnnouncementCrawler(BaseCrawler):
    _CNINFO_TYPE_MAP: Dict[str, str] = {
        "010101": "financial_report",
        "010102": "financial_report",
        "010103": "financial_report",
        "010106": "financial_report",
        "010107": "financial_report",
        "010201": "restructuring",
        "010202": "equity",
        "010203": "equity",
        "010301": "dividend",
        "010401": "shareholder",
        "010501": "management",
        "010601": "litigation",
        "010701": "risk",
    }
    _CNINFO_TYPE_PREFIX_MAP: Dict[str, str] = {
        "0101": "company_operation",
        "0102": "equity",
        "0103": "dividend",
        "0104": "shareholder",
        "0105": "governance",
        "0106": "litigation",
        "0107": "risk",
        "011": "exchange_disclosure",
        "012": "special_matter",
        "013": "other_disclosure",
    }

    def __init__(self, output_dir: str = "data/raw/announcements"):
        super().__init__(output_dir)

    def get_required_fields(self) -> List[str]:
        return ["title", "stock_code", "publish_date"]

    def fetch(
        self,
        stock_codes: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_announcements: int = 5000,
        enable_cninfo_fallback: bool = True,
    ) -> List[Dict]:
        rows: List[Dict] = []

        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

        logger.info(f"Fetching announcements: {start_date} -> {end_date}")

        if stock_codes:
            for code in stock_codes:
                part = self._fetch_stock_announcements(code, start_date, end_date)
                rows.extend(part)
                logger.info(f"Fetched {len(part)} rows for stock {code}")
        else:
            rows.extend(self._fetch_all_announcements(start_date, end_date))

        if enable_cninfo_fallback and self._needs_cninfo_fallback(rows):
            logger.info("Low link/content coverage from AKShare. Switching to cninfo fallback source.")
            if stock_codes:
                fallback_rows: List[Dict] = []
                for code in stock_codes:
                    fallback_rows.extend(self._fetch_cninfo_stock_announcements(code, start_date, end_date))
            else:
                fallback_rows = self._fetch_cninfo_announcements(start_date, end_date, max_announcements)
            if fallback_rows:
                rows = fallback_rows

        if len(rows) > max_announcements:
            rows = rows[:max_announcements]

        logger.info(f"Total announcements fetched: {len(rows)}")
        return rows

    def _fetch_all_announcements(self, start_date: str, end_date: str) -> List[Dict]:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        rows: List[Dict] = []
        cur = start
        while cur <= end:
            date_key = cur.strftime("%Y%m%d")
            try:
                df = ak.stock_notice_report(date=date_key)
                if df is not None and not df.empty:
                    rows.extend(df.to_dict("records"))
                    logger.debug(f"{date_key}: {len(df)} rows")
                else:
                    logger.debug(f"{date_key}: empty response (holiday or no data)")
            except KeyError as exc:
                logger.debug(f"{date_key}: no data (KeyError: {exc}, likely holiday/non-trading day)")
            except Exception as exc:
                logger.warning(f"AKShare fetch failed for {date_key}: {exc}")
            cur += timedelta(days=1)
        return rows

    def _fetch_stock_announcements(self, stock_code: str, start_date: str, end_date: str) -> List[Dict]:
        # Prefer API with symbol support.
        if hasattr(ak, "stock_notice_report_em"):
            try:
                df = ak.stock_notice_report_em(symbol=stock_code)
                if df is not None and not df.empty:
                    return self._filter_by_date(df.to_dict("records"), start_date, end_date)
            except Exception as exc:
                logger.warning(f"AKShare stock_notice_report_em failed for {stock_code}: {exc}")
        else:
            logger.debug("AKShare has no stock_notice_report_em in current version; use fallback path.")

        # Fallback: pull by date range then filter by stock code.
        rows = self._fetch_all_announcements(start_date, end_date)
        filtered: List[Dict] = []
        for row in rows:
            code = self._get_stock_code(row)
            if code == stock_code:
                filtered.append(row)

        # Last fallback: cninfo stock-specific query.
        if not filtered:
            logger.info(f"AKShare returned 0 rows for {stock_code}, trying cninfo stock-specific query.")
            filtered = self._fetch_cninfo_stock_announcements(stock_code, start_date, end_date)
        return filtered

    def _fetch_cninfo_stock_announcements(self, stock_code: str, start_date: str, end_date: str) -> List[Dict]:
        endpoint = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
        }
        se_date = f"{start_date}~{end_date}"

        rows: List[Dict] = []
        page_num = 1
        page_size = 30
        while True:
            payload = {
                "pageNum": page_num,
                "pageSize": page_size,
                "column": "szse",
                "tabName": "fulltext",
                "plate": "",
                "stock": f"{stock_code},",
                "searchkey": "",
                "secid": "",
                "category": "",
                "trade": "",
                "seDate": se_date,
                "sortName": "",
                "sortType": "",
                "isHLtitle": "true",
            }
            try:
                resp = requests.post(endpoint, data=payload, headers=headers, timeout=20)
                if resp.status_code != 200:
                    break
                data = resp.json()
                part = data.get("announcements", []) or []
                if not part:
                    break
                rows.extend(part)
                total_pages = int(data.get("totalpages", 0) or 0)
                if total_pages and page_num >= total_pages:
                    break
                page_num += 1
            except Exception as exc:
                logger.warning(f"cninfo stock query failed at page {page_num} for {stock_code}: {exc}")
                break

        filtered = [r for r in rows if self._get_stock_code(r) == stock_code]
        if filtered:
            logger.info(f"cninfo stock-specific rows for {stock_code}: {len(filtered)}")
            return filtered

        # Fallback 2: use searchkey and post-filter again.
        logger.info(f"cninfo stock payload returned 0 exact rows for {stock_code}; try searchkey fallback.")
        rows2: List[Dict] = []
        page_num = 1
        while True:
            payload = {
                "pageNum": page_num,
                "pageSize": page_size,
                "column": "szse",
                "tabName": "fulltext",
                "plate": "",
                "stock": "",
                "searchkey": stock_code,
                "secid": "",
                "category": "",
                "trade": "",
                "seDate": se_date,
                "sortName": "",
                "sortType": "",
                "isHLtitle": "true",
            }
            try:
                resp = requests.post(endpoint, data=payload, headers=headers, timeout=20)
                if resp.status_code != 200:
                    break
                data = resp.json()
                part = data.get("announcements", []) or []
                if not part:
                    break
                rows2.extend(part)
                total_pages = int(data.get("totalpages", 0) or 0)
                if total_pages and page_num >= total_pages:
                    break
                page_num += 1
            except Exception as exc:
                logger.warning(f"cninfo searchkey query failed at page {page_num} for {stock_code}: {exc}")
                break

        filtered2 = [r for r in rows2 if self._get_stock_code(r) == stock_code]
        logger.info(f"cninfo searchkey rows for {stock_code}: {len(filtered2)}")
        return filtered2

    def _fetch_cninfo_announcements(self, start_date: str, end_date: str, max_announcements: int) -> List[Dict]:
        endpoint = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
        }
        se_date = f"{start_date}~{end_date}"

        rows: List[Dict] = []
        page_num = 1
        page_size = 30
        while len(rows) < max_announcements:
            payload = {
                "pageNum": page_num,
                "pageSize": page_size,
                "column": "szse",
                "tabName": "fulltext",
                "plate": "",
                "stock": "",
                "searchkey": "",
                "secid": "",
                "category": "",
                "trade": "",
                "seDate": se_date,
                "sortName": "",
                "sortType": "",
                "isHLtitle": "true",
            }
            try:
                resp = requests.post(endpoint, data=payload, headers=headers, timeout=20)
                if resp.status_code != 200:
                    break
                data = resp.json()
                part = data.get("announcements", []) or []
                if not part:
                    break
                rows.extend(part)
                total_pages = int(data.get("totalpages", 0) or 0)
                if total_pages and page_num >= total_pages:
                    break
                page_num += 1
            except Exception as exc:
                logger.warning(f"cninfo fallback failed at page {page_num}: {exc}")
                break

        logger.info(f"cninfo fallback rows: {len(rows)}")
        return rows

    def _needs_cninfo_fallback(self, rows: List[Dict]) -> bool:
        if not rows:
            return True
        sample = rows[: min(200, len(rows))]
        covered = 0
        for row in sample:
            if self._get_url(row) or self._get_pdf_url(row) or self._get_content(row):
                covered += 1
        ratio = covered / max(1, len(sample))
        logger.info(f"AKShare link/content coverage: {ratio:.2%}")
        return ratio < 0.05

    def _extract_date(self, row: Dict) -> Optional[str]:
        keys = ["publish_date", "date", "announcement_date", "announcementTime", "time", "publishTime", "公告日期", "日期"]
        for key in keys:
            if key not in row:
                continue
            value = row.get(key)
            if value is None:
                continue

            if isinstance(value, (int, float)):
                if value > 10_000_000_000:
                    return datetime.fromtimestamp(value / 1000).strftime("%Y-%m-%d")
                if value > 1_000_000_000:
                    return datetime.fromtimestamp(value).strftime("%Y-%m-%d")

            txt = str(value).strip()
            if not txt:
                continue
            if txt.isdigit():
                ts = int(txt)
                if ts > 10_000_000_000:
                    return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
                if ts > 1_000_000_000:
                    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
                try:
                    return datetime.strptime(txt, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    pass
        return None

    def _filter_by_date(self, rows: List[Dict], start_date: str, end_date: str) -> List[Dict]:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        filtered: List[Dict] = []
        for row in rows:
            date_str = self._extract_date(row)
            if not date_str:
                filtered.append(row)
                continue
            try:
                day = datetime.strptime(date_str, "%Y-%m-%d")
                if start <= day <= end:
                    filtered.append(row)
            except ValueError:
                filtered.append(row)
        return filtered

    def parse(self, raw_data: List[Dict]) -> List[Dict]:
        parsed: List[Dict] = []
        for row in raw_data:
            try:
                parsed.append(self._parse_single_announcement(row))
            except Exception as exc:
                logger.warning(f"Parse failed: {exc}")
        return parsed

    def _pick(self, row: Dict, candidates: List[str]) -> str:
        for key in candidates:
            v = row.get(key)
            if v is not None and str(v).strip():
                return str(v).strip()
        lowered = [(str(k), str(k).lower()) for k in row.keys()]
        for key, low in lowered:
            if any(c.lower() in low for c in candidates):
                v = row.get(key)
                if v is not None and str(v).strip():
                    return str(v).strip()
        return ""

    def _get_title(self, row: Dict) -> str:
        return self._pick(row, ["title", "announcementTitle", "notice_title", "short_name", "公告标题", "标题"])

    def _get_stock_code(self, row: Dict) -> str:
        return self._pick(row, ["stock_code", "symbol", "secCode", "stockCode", "code", "sec_code", "代码", "股票代码", "证券代码"])

    def _get_stock_name(self, row: Dict) -> str:
        return self._pick(row, ["stock_name", "name", "secName", "sec_name", "简称", "股票简称", "证券简称"])

    def _map_cninfo_type_code(self, value: str) -> str:
        v = str(value).strip()
        if not v:
            return ""
        if v.isdigit() and len(v) == 6:
            return self._CNINFO_TYPE_MAP.get(v, "other")
        # cninfo may return combined code string: 01010503||010112||...
        parts = re.split(r"[|,;/\s]+", v)
        mapped: List[str] = []
        for p in parts:
            p = p.strip()
            if p.isdigit():
                if len(p) == 6:
                    mapped.append(self._CNINFO_TYPE_MAP.get(p, "other"))
                elif len(p) > 6:
                    # Prefer exact 6-digit map, then prefix map.
                    m = self._CNINFO_TYPE_MAP.get(p[:6], "")
                    if not m:
                        m = self._CNINFO_TYPE_PREFIX_MAP.get(p[:4], "")
                    if not m:
                        m = self._CNINFO_TYPE_PREFIX_MAP.get(p[:3], "")
                    if m:
                        mapped.append(m)
        mapped = [m for m in mapped if m and m != "other"]
        if mapped:
            return mapped[0]
        return ""

    def _get_type(self, row: Dict, title: str) -> str:
        value = self._pick(
            row,
            [
                "announcement_type",
                "type",
                "notice_type",
                "announcementTypeName",
                "announcementType",
                "公告类型",
                "通知类型",
            ],
        )
        if value:
            mapped = self._map_cninfo_type_code(value)
            if mapped:
                return mapped
            # Keep original type string when no mapping is available to avoid information loss.
            return value
        return self._classify_type(title)

    def _normalize_cninfo_path(self, value: str) -> str:
        if not value:
            return ""
        v = value.strip()
        if v.startswith("http://") or v.startswith("https://"):
            return v
        if v.startswith("/"):
            return f"http://static.cninfo.com.cn{v}"
        return f"http://static.cninfo.com.cn/{v}"

    def _get_url(self, row: Dict) -> str:
        value = self._pick(row, ["url", "link", "notice_url", "announcementUrl", "adjunctUrl", "公告链接"])
        return self._normalize_cninfo_path(value)

    def _get_pdf_url(self, row: Dict) -> str:
        value = self._pick(row, ["pdf_url", "adjunctUrl", "pdf", "PDF链接", "附件链接"])
        return self._normalize_cninfo_path(value)

    def _get_content(self, row: Dict) -> str:
        return self._pick(row, ["content", "summary", "notice_content", "article", "公告内容", "摘要", "正文"])

    def _parse_single_announcement(self, row: Dict) -> Dict:
        title = self._get_title(row)
        stock_code = self._get_stock_code(row)
        stock_name = self._get_stock_name(row)
        ann_type = self._get_type(row, title)
        publish_date = self._extract_date(row) or datetime.now().strftime("%Y-%m-%d")
        url = self._get_url(row)
        pdf_url = self._get_pdf_url(row)
        content = self._get_content(row)

        ann_id = hashlib.sha1(f"{stock_code}|{publish_date}|{title}|{url}|{pdf_url}".encode("utf-8")).hexdigest()

        return {
            "id": ann_id,
            "title": title,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "announcement_type": ann_type,
            "publish_date": publish_date,
            "content": content,
            "url": url,
            "pdf_url": pdf_url,
            "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _classify_type(self, title: str) -> str:
        rules = {
            "financial_report": ["年报", "半年报", "季报", "业绩", "财务"],
            "restructuring": ["重组", "并购", "收购", "出售"],
            "dividend": ["分红", "派息", "送转"],
            "equity": ["增发", "配股", "定增"],
            "litigation": ["诉讼", "仲裁"],
            "management": ["董事", "高管", "任命", "辞职"],
            "shareholder": ["股东", "持股", "减持", "增持"],
            "risk": ["风险", "提示", "警示"],
        }
        for typ, words in rules.items():
            if any(w in title for w in words):
                return typ
        return "other"
