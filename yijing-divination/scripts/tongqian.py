#!/usr/bin/env python3
"""
铜钱法模拟 —— 模拟三枚铜钱投掷六次，生成六爻。

用法：
    python tongqian.py              # 输出六行结果（6/7/8/9）
    python tongqian.py --json       # JSON 格式输出（供 skill 调用）

输出说明：
    6 = 老阴（动爻）
    7 = 少阳（静爻）
    8 = 少阴（静爻）
    9 = 老阳（动爻）

参考：
    京房易传 · 铜钱法（三钱法）
"""

import random
import json
import sys


def cast_one_line() -> int:
    """投掷三枚铜钱，返回结果（6/7/8/9）"""
    coins = [random.randint(0, 1) for _ in range(3)]
    s = sum(coins)
    if s == 0:
        return 6   # 老阴
    elif s == 1:
        return 7   # 少阳
    elif s == 2:
        return 8   # 少阴
    else:
        return 9   # 老阳


def full_cast(verbose: bool = False) -> list[dict]:
    """执行完整六爻投掷，返回列表（初爻→上爻）"""
    lines = []
    for i in range(6):
        value = cast_one_line()
        label = {6: "老阴", 7: "少阳", 8: "少阴", 9: "老阳"}[value]
        is_moving = value in (6, 9)
        record = {
            "position": i + 1,
            "name": f"{'初九' if i == 0 else '上九' if i == 5 else f'九{i+1}' if value in (7, 9) else '初六' if i == 0 else '上六' if i == 5 else f'六{i+1}'}",
            "value": value,
            "yin": value in (6, 8),
            "yang": value in (7, 9),
            "moving": is_moving,
            "label": label,
        }
        lines.append(record)
        if verbose:
            print(f"第{i+1}爻: {label} (值={value})")
    return lines


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv
    as_json = "--json" in sys.argv

    result = full_cast(verbose=verbose)

    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for line in result:
            print(line["value"])
