#!/usr/bin/env python3
"""
大六壬起课 —— 占时、月将、天地盘、日干支（四课三传须参照 references 九宗门手断或后续扩展）。

用法：
    py -3 daliuren_pan.py 2026-07-04 06:00
    py -3 daliuren_pan.py --datetime "2026-07-04 06:00" --json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

YIJING_SCRIPTS = Path(__file__).resolve().parent.parent.parent / "yijing-divination" / "scripts"
sys.path.insert(0, str(YIJING_SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ganzhi import compute as ganzhi_compute, DIZHI

# 月将（中气后）近似公历起始 (月, 日) → (月将名, 地支)
YUE_JIANG = [
    (1, 20, "神后", "子"), (2, 19, "登明", "亥"), (3, 21, "河魁", "戌"),
    (4, 20, "从魁", "酉"), (5, 21, "传送", "申"), (6, 22, "小吉", "未"),
    (7, 23, "胜光", "午"), (8, 23, "太乙", "巳"), (9, 23, "天罡", "辰"),
    (10, 24, "太冲", "卯"), (11, 22, "功曹", "寅"), (12, 22, "大吉", "丑"),
]

YUE_JIANG_NAMES = {
    "子": "神后", "亥": "登明", "戌": "河魁", "酉": "从魁", "申": "传送", "未": "小吉",
    "午": "胜光", "巳": "太乙", "辰": "天罡", "卯": "太冲", "寅": "功曹", "丑": "大吉",
}


def shichen(hour: int) -> tuple[str, int]:
    if hour == 23 or hour == 0:
        return "子", 0
    return DIZHI[(hour + 1) // 2], (hour + 1) // 2


def yue_jiang_for_date(month: int, day: int) -> tuple[str, str]:
    result = ("神后", "子")
    for m, d, name, dz in YUE_JIANG:
        if (month > m) or (month == m and day >= d):
            result = (name, dz)
    return result


def build_tiandi_pan(yue_dz: str, hour_dz: str) -> dict:
    """月将加占时，顺行十二辰。返回地盘→天盘映射。"""
    start = DIZHI.index(hour_dz)
    yue_idx = DIZHI.index(yue_dz)
    pan = {}
    for i, di in enumerate(DIZHI):
        pos = (start + i) % 12
        pan[di] = DIZHI[(yue_idx + i) % 12]
    return pan


def parse_dt(text: str) -> datetime:
    text = text.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(text)


def compute(dt: datetime) -> dict:
    sc_name, _ = shichen(dt.hour)
    yj_name, yj_dz = yue_jiang_for_date(dt.month, dt.day)
    gz = ganzhi_compute(dt.date())
    pan = build_tiandi_pan(yj_dz, sc_name)
    return {
        "占时": dt.strftime("%Y-%m-%d %H:%M"),
        "时辰": sc_name,
        "月将": {"名": yj_name, "地支": yj_dz},
        "日干支": gz,
        "天地盘": {f"地盘{k}": f"天盘{v}({YUE_JIANG_NAMES.get(v, v)})" for k, v in pan.items()},
        "说明": "四课、三传、九宗门请结合 references/sike-sanchuan.md 在课体基础上继续；本脚本仅自动化天地盘。",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("datetime_pos", nargs="?", help="2026-07-04 06:00")
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
        print(f"占时: {r['占时']}  时辰:{r['时辰']}")
        print(f"月将: {r['月将']['名']}({r['月将']['地支']})  日干支:{r['日干支']['日干支']}")
        print("天地盘(地盘→天盘):")
        for k, v in r["天地盘"].items():
            print(f"  {k} → {v}")


if __name__ == "__main__":
    main()
