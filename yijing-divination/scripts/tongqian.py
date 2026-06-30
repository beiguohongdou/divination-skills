#!/usr/bin/env python3
"""
铜钱法 / 数字法起卦 —— 模拟铜钱或三数起卦，输出本卦、变卦、互卦、体用。

用法：
    py -3 tongqian.py                    # 铜钱法，输出 6/7/8/9
    py -3 tongqian.py --json             # 铜钱 + 卦象 JSON
    py -3 tongqian.py --nums 105 372 891 --json   # 数字法
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hexagram_core import (  # noqa: E402
    digital_cast,
    hex_from_coin_values,
    ti_yong_from_moving,
)


def cast_one_line() -> int:
    coins = [random.randint(0, 1) for _ in range(3)]
    s = sum(coins)
    return {0: 6, 1: 7, 2: 8, 3: 9}[s]


def full_cast(verbose: bool = False) -> list[dict]:
    lines = []
    labels = {6: "老阴", 7: "少阳", 8: "少阴", 9: "老阳"}
    for i in range(6):
        value = cast_one_line()
        is_moving = value in (6, 9)
        yin = value in (6, 8)
        if i == 0:
            name = "初六" if yin else "初九"
        elif i == 5:
            name = "上六" if yin else "上九"
        else:
            name = ("六" if yin else "九") + ["", "二", "三", "四", "五"][i]
        record = {
            "position": i + 1,
            "name": name,
            "value": value,
            "yin": yin,
            "yang": not yin,
            "moving": is_moving,
            "label": labels[value],
        }
        lines.append(record)
        if verbose:
            print(f"第{i+1}爻: {labels[value]} (值={value})")
    return lines


def build_result_from_values(values: list[int], method: str) -> dict:
    pan = hex_from_coin_values(values)
    ty = ti_yong_from_moving(pan["动爻"], pan["binary"])
    return {
        "起卦方式": method,
        "六爻": values,
        "六爻明细": [
            {"爻位": i + 1, "值": v, "动": v in (6, 9)} for i, v in enumerate(values)
        ],
        **pan,
        "体用": ty,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="铜钱法 / 数字法起卦")
    p.add_argument("--json", action="store_true")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--nums", nargs=3, type=int, metavar="N", help="数字法三数")
    p.add_argument("--question", "-q", default="", help="问事（写入日志）")
    p.add_argument("--log-id", help="追加到已有日志目录")
    args = p.parse_args()

    if args.nums:
        pan = digital_cast(tuple(args.nums))
        ty = ti_yong_from_moving(pan["动爻"], pan["binary"])
        result = {"起卦方式": "数字法", **pan, "体用": ty}
    else:
        cast = full_cast(verbose=args.verbose)
        values = [c["value"] for c in cast]
        result = build_result_from_values(values, "铜钱法")
        if not args.json and not args.verbose:
            for v in values:
                print(v)

    try:
        from _log_hook import attach_session_log, inject_log_into_result  # noqa: E402

        method = "tongqian_nums" if args.nums else "tongqian_coin"
        log_info = attach_session_log(
            system="yijing",
            method=method,
            payload=result,
            question=args.question,
            script="tongqian.py",
            log_id=args.log_id,
        )
        result = inject_log_into_result(result, log_info)
    except Exception:
        pass

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.nums or args.verbose:
        ben = result["本卦"]
        print(f"本卦: {ben['name']}  变卦: {result['变卦']['name'] if result.get('变卦') else '无'}")
        print(f"互卦: {result['互卦']['name']}  动爻: {result['动爻']}")
        print(f"体用: {result['体用']['体卦']} / {result['体用']['用卦']} → {result['体用']['生克']}")
        if result.get("_session_log"):
            lg = result["_session_log"]
            print(f"[日志] id={lg['id']}  dir={lg['dir']}")


if __name__ == "__main__":
    main()
