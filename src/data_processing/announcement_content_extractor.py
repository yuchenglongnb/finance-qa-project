"""
Announcement content extraction utilities.
"""
from __future__ import annotations

import io
import logging
import re
from typing import Optional

import pdfplumber
import requests
from bs4 import BeautifulSoup

# Reduce noisy decode warnings from pdfminer.
logging.getLogger("pdfminer").setLevel(logging.ERROR)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_replacement_chars(text: str) -> str:
    """
    Remove low-quality lines with too many U+FFFD replacement characters.
    """
    if not text:
        return text
    lines = text.split("\n")
    kept = []
    for line in lines:
        total = len(line)
        if total == 0:
            continue
        bad = line.count("\ufffd")
        if bad / total > 0.3:
            continue
        kept.append(line.replace("\ufffd", ""))
    return "\n".join(kept)


def fetch_bytes(url: str, timeout: int = 20) -> Optional[bytes]:
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            return None
        return resp.content
    except Exception:
        return None


def extract_text_from_pdf_bytes(data: bytes, max_chars: int = 8000, max_pages: int = 8) -> str:
    if not data:
        return ""
    parts = []
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for idx, page in enumerate(pdf.pages):
                if idx >= max_pages:
                    break
                try:
                    text = page.extract_text() or ""
                except Exception:
                    continue
                text = clean_replacement_chars(text)
                text = normalize_whitespace(text)
                if text:
                    parts.append(text)
                if sum(len(x) for x in parts) >= max_chars:
                    break
    except Exception:
        return ""
    return normalize_whitespace(" ".join(parts))[:max_chars]


def extract_text_from_html_bytes(data: bytes, max_chars: int = 8000) -> str:
    if not data:
        return ""
    try:
        soup = BeautifulSoup(data, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = normalize_whitespace(soup.get_text(separator=" "))
        return text[:max_chars]
    except Exception:
        return ""
