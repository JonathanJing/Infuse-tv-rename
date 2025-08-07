#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilities for extracting clean show/series titles from filenames.
"""

from pathlib import Path
import re


def _clean_bracket_groups(text: str) -> str:
    # Remove content inside common bracket types
    return re.sub(r"[\[\(【（].*?[\]\)】）]", " ", text)


def _replace_delimiters_with_space(text: str) -> str:
    # Replace common delimiters with spaces
    text = re.sub(r"[._\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _strip_common_markers(text: str) -> str:
    # Remove common quality/codec/source and language markers and years
    junk_patterns = [
        r"\b720p\b", r"\b1080p\b", r"\b2160p\b", r"\b4k\b", r"\b8k\b",
        r"\bhd\b", r"\buhd\b", r"\bhdtv\b", r"\bwebrip\b", r"\bweb\-?dl\b",
        r"\bbluray\b", r"\bbdrip\b", r"\bdvdrip\b", r"\bremux\b",
        r"\bx264\b", r"\bx265\b", r"h\.?264", r"h\.?265", r"\bhevc\b", r"\bavc\b",
        r"\bdolby\b", r"\batmos\b", r"\bdts\b", r"\baac\b", r"\bac3\b",
        r"\brepack\b", r"\bproper\b", r"\bextended\b", r"directors\s*cut",
        r"theatrical",
        r"chs?ub", r"中字", r"双语", r"国配", r"国英", r"内封", r"外挂", r"简繁", r"繁英", r"简英",
        r"\b(19|20)\d{2}\b",
    ]
    pattern = re.compile("|".join(junk_patterns), flags=re.IGNORECASE)
    text = pattern.sub(" ", text)
    return _replace_delimiters_with_space(text)


def _left_of_first_marker(text: str) -> str:
    # Cut the string at the earliest season/episode marker occurrence
    markers = [
        r"[Ss]\d{1,2}[Ee]\d{1,3}",  # S01E01
        r"[Ee]\d{1,3}",              # E01
        r"第\s*\d+\s*季",           # 第1季
        r"第\s*\d+\s*集",           # 第1集
        r"Season\s*\d+",            # Season 1
        r"\bS\d{1,2}\b",           # S01
        r"\bEP?\d{1,3}\b",         # E1/EP1
    ]
    earliest = None
    for pat in markers:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            if earliest is None or m.start() < earliest:
                earliest = m.start()
    if earliest is not None:
        return text[:earliest]
    return text


def extract_series_title_from_filename(filename: str, fallback: str = "") -> str:
    """
    Extract a likely series/show title from a raw filename.

    This keeps the original naming style as much as possible while removing
    obvious noise such as quality tags, codecs, and season/episode markers.
    """
    stem = Path(filename).stem
    candidate = stem

    # Remove bracketed groups which are often release tags or groups
    candidate = _clean_bracket_groups(candidate)

    # If there are known markers (SxxEyy, 第xx季/集, etc.), keep the left part
    candidate = _left_of_first_marker(candidate)

    # Remove common junk terms
    candidate = _strip_common_markers(candidate)

    # Final normalization of delimiters and whitespace
    candidate = _replace_delimiters_with_space(candidate)

    # Trim trailing season words if they remain
    candidate = re.sub(r"(第\s*\d+\s*季)$", "", candidate).strip()
    candidate = re.sub(r"(Season\s*\d+)$", "", candidate, flags=re.IGNORECASE).strip()

    if candidate:
        return candidate
    return fallback or stem

