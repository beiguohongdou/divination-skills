#!/usr/bin/env python3
"""
奇门遁甲 · 时家奇门定局 —— 按节气近似日定阴阳遁与局数（全排盘见 references/shiwei-pan.md）。

用法：
    py -3 qimen_pan.py 2026-07-04 06:00 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 节气近似起始 (月,日): (节气名, 阳遁局, 阴遁局) — 来自 SKILL 定局口诀
# 每项：过了此日进入该节气段；阳遁用阳局，阴遁用阴局（夏至后阴遁）
JIEQI_TABLE = [
    (12, 22, "冬至", 1, None),
    (1, 6, "小寒", 2, None),
    (1, 20, "大寒", 3, None),
    (2, 4, "立春", 8, None),
    (2, 19, "雨水", 9, None),
    (3, 6, "惊蛰", 1, None),
    (3, 21, "春分", 3, None),
    (4, 5, "清明", 4, None),
    (4, 20, "谷雨", 5, None),
    (5, 6, "立夏", 4, None),
    (5, 21, "小满", 5, None),
    (6, 6, "芒种", 6, None),
    (6, 22, "夏至", None, 9),
    (7, 7, "小暑", None, 8),
    (7, 23, "大暑", None, 7),
    (8, 8, "立秋", None, 2),
    (8, 23, "处暑", None, 1),
    (9, 8, "白露", None, 9),
    (9, 23, "秋分", None, 7),
    (10, 8, "寒露", None, 6),
    (10, 23, "霜降", None, 5),
    (11, 7, "立冬", None, 6),
    (11, 22, "小雪", None, 5),
    (12, 7, "大雪", None, 4),
]

DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def shichen(hour: int) -> str:
    if hour == 23 or hour == 0:
        return "子"
    return DIZHI[(hour + 1) // 2]


def ding_ju(month: int, day: int) -> dict:
    name, yang, yin = "冬至", 1, None
    for m, d, jn, yg, ying in JIEQI_TABLE:
        if (month > m) or (month == m and day >= d):
            name, yang, yin = jn, yg, ying
    if yang is not None:
        return {"节气": name, "遁": "阳遁", "局数": yang}
    return {"节气": name, "遁": "阴遁", "局数": yin}


def parse_dt(text: str) -> datetime:
    text = text.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(text)


def compute(dt: datetime) -> dict:
    dj = ding_ju(dt.month, dt.day)
    return {
        "时间": dt.strftime("%Y-%m-%d %H:%M"),
        "时辰": shichen(dt.hour),
        "定局": dj,
        "说明": "本脚本仅定局；九宫排盘（地盘天盘八门九星八神）请参照 references/shiwei-pan.md 逐步排或待后续 qimen 全排脚本。",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("datetime_pos", nargs="?")
    p.add_argument("time_pos", nargs="?")
    p.add_argument("-d", "--datetime")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    if args.datetime:
        dt = parse_dt(args.datetime)
    elif args.datetime_pos:
        s = args.datetime_pos if not args.time_pos else f"{args.datetime_pos} {args.time_pos}"
        dt = parse_dt(s)
    else:
        dt = datetime.now()

    r = compute(dt)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        dj = r["定局"]
        print(f"{r['时间']}  {r['时辰']}时  节气≈{dj['节气']}  {dj['遁']}{dj['局数']}局")


if __name__ == "__main__":
    main()
