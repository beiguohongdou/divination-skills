#!/usr/bin/env python3
"""
大六壬起课 —— 薄封装，委托 daliuren.py 全排盘（四课、三传、天将）。

用法（与 meihua_time 一致）：
    py -3 daliuren_pan.py 2026-07-04 06:00
    py -3 daliuren_pan.py --datetime "2026-07-04 06:00" --json

完整排盘请优先使用同目录 daliuren.py（本脚本与其等价）。
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
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from daliuren import compute, format_output  # noqa: E402


def parse_dt(text: str) -> datetime:
    text = text.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析时间: {text!r}")


def main() -> None:
    p = argparse.ArgumentParser(description="大六壬全排盘（委托 daliuren.py）")
    p.add_argument("datetime_pos", nargs="?", help="如 2026-07-04 06:00")
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

    result = compute(dt)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_output(result))


if __name__ == "__main__":
    main()
