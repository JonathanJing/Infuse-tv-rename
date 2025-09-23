#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilities for extracting clean show/series titles from filenames.
"""

from pathlib import Path
import re
from typing import Optional


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


# ---------------------- Episode index extraction helpers ----------------------

# 支持常见中文数字，包括简体、常用财务大写、特殊 20/30（廿/卅）、两
_CHN_DIGITS = {
    "零": 0, "〇": 0,
    "一": 1, "壹": 1,
    "二": 2, "贰": 2, "两": 2,
    "三": 3, "叁": 3,
    "四": 4, "肆": 4,
    "五": 5, "伍": 5,
    "六": 6, "陆": 6,
    "七": 7, "柒": 7,
    "八": 8, "捌": 8,
    "九": 9, "玖": 9,
}
_CHN_UNITS = {
    "十": 10, "拾": 10,
    "百": 100, "佰": 100,
    "千": 1000, "仟": 1000,
    "万": 10000,
}

# 全角数字转半角数字映射
_FULLWIDTH_TO_ASCII = str.maketrans({
    "０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
    "５": "5", "６": "6", "７": "7", "８": "8", "９": "9",
})


def _chinese_numeral_to_int(text: str) -> Optional[int]:
    """
    将中文数字转为阿拉伯数字，支持到万级，例如：三十一、一百二十三、两千零五、第三十一回。
    仅处理数字字符部分，调用方应先剥离“第”“集/回”等修饰。
    返回 None 表示无法解析。
    """
    if not text:
        return None
    # 处理特殊词：廿(20)、卅(30)、卌(40)
    text = text.strip()
    special_map = {"廿": 20, "卅": 30, "卌": 40}
    if text in special_map:
        return special_map[text]

    # 如果包含阿拉伯数字，直接解析连续数字
    m = re.search(r"\d+", text)
    if m:
        try:
            return int(m.group())
        except ValueError:
            return None

    # 分段按“万”处理：高位*10000 + 低位
    def parse_under_10000(seg: str) -> Optional[int]:
        if not seg:
            return 0
        total = 0
        last_unit = 1
        num_buffer = None  # 最近一个数字

        # 如果没有任何单位，可能是简单数字串："三"、"两"、"三二"(很少见)
        if all(ch not in _CHN_UNITS for ch in seg):
            val = 0
            for ch in seg:
                if ch in _CHN_DIGITS:
                    val = val * 10 + _CHN_DIGITS[ch]
                else:
                    # 遇到未知字符，无法解析
                    return None
            return val

        i = 0
        length = len(seg)
        while i < length:
            ch = seg[i]
            if ch in _CHN_DIGITS:
                num_buffer = _CHN_DIGITS[ch]
                i += 1
            elif ch in _CHN_UNITS:
                unit_val = _CHN_UNITS[ch]
                # "十"开头等价于 1*10
                if num_buffer is None:
                    num_buffer = 1
                total += num_buffer * unit_val
                num_buffer = None
                last_unit = unit_val
                i += 1
            elif ch == "零":
                # 跳过占位的零
                i += 1
            else:
                # 未知字符
                return None

        # 没有单位跟随的尾数
        if num_buffer is not None:
            total += num_buffer

        return total

    if "万" in text:
        parts = text.split("万", 1)
        high = parse_under_10000(parts[0])
        low = parse_under_10000(parts[1])
        if high is None or low is None:
            return None
        return high * 10000 + low
    else:
        return parse_under_10000(text)


def extract_episode_index_from_filename(filename: str) -> Optional[int]:
    """
    从文件名中提取用于排序的集数索引。
    优先规则：
    1) "第[中文数字]([集回话讲篇期部])" → 中文转数字
    2) "第\d+([集回话讲篇期部])" → 直接数字
    3) SxxEyy/Eyy → 取 E 后数字
    4) 末尾（或靠后）孤立数字 → 作为候选
    无法解析返回 None。
    """
    name = Path(filename).stem
    # 标准化全角数字
    text = name.translate(_FULLWIDTH_TO_ASCII)

    # 1) 第三十一集/回
    m = re.search(r"第\s*([一二三四五六七八九十百千万两〇零廿卅卌壹贰叁肆伍陆柒捌玖拾佰仟万]+)\s*[集回话讲篇期部卷]", text)
    if m:
        val = _chinese_numeral_to_int(m.group(1))
        if isinstance(val, int):
            return val

    # 2) 第31集/回
    m = re.search(r"第\s*(\d{1,4})\s*[集回话讲篇期部卷]", text)
    if m:
        return int(m.group(1))

    # 3) SxxEyy / Eyy / EPyy
    m = re.search(r"[Ss]\d{1,2}[Ee](\d{1,4})", text)
    if m:
        return int(m.group(1))
    m = re.search(r"\bE[Pp]?(\d{1,4})\b", text)
    if m:
        return int(m.group(1))

    # 4) 尝试靠后的孤立数字（避免年份等，选最后一个且在 1..999 之间）
    nums = re.findall(r"(\d{1,4})", text)
    for token in reversed(nums):
        n = int(token)
        if 1 <= n <= 999:
            return n

    return None

