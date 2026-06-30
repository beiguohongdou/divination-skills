#!/usr/bin/env python3
"""
卦象共用逻辑 —— 互卦、铜钱/数字法定卦、体用（供 meihua_time / tongqian / shufa 调用）。
"""

from __future__ import annotations

TRIGRAM = {
    "乾": "111", "兑": "110", "离": "101", "震": "100",
    "巽": "011", "坎": "010", "艮": "001", "坤": "000",
}
BITS_TRIGRAM = {v: k for k, v in TRIGRAM.items()}
BIT3_MAP = {"111": 1, "110": 2, "101": 3, "100": 4, "011": 5, "010": 6, "001": 7, "000": 8}

WUXING = {"乾": "金", "兑": "金", "离": "火", "震": "木", "巽": "木", "坎": "水", "艮": "土", "坤": "土"}

HEXAGRAMS: dict[tuple[str, str], tuple[int, str]] = {
    ("乾", "乾"): (1, "乾为天"), ("坤", "坤"): (2, "坤为地"),
    ("坎", "震"): (3, "水雷屯"), ("艮", "坎"): (4, "山水蒙"),
    ("坎", "乾"): (5, "水天需"), ("乾", "坎"): (6, "天水讼"),
    ("坤", "坎"): (7, "地水师"), ("坎", "坤"): (8, "水地比"),
    ("巽", "乾"): (9, "风天小畜"), ("乾", "兑"): (10, "天泽履"),
    ("坤", "乾"): (11, "地天泰"), ("乾", "坤"): (12, "天地否"),
    ("乾", "离"): (13, "天火同人"), ("离", "乾"): (14, "火天大有"),
    ("坤", "艮"): (15, "地山谦"), ("震", "坤"): (16, "雷地豫"),
    ("兑", "震"): (17, "泽雷随"), ("艮", "巽"): (18, "山风蛊"),
    ("坤", "兑"): (19, "地泽临"), ("巽", "坤"): (20, "风地观"),
    ("离", "震"): (21, "火雷噬嗑"), ("艮", "离"): (22, "山火贲"),
    ("艮", "坤"): (23, "山地剥"), ("坤", "震"): (24, "地雷复"),
    ("乾", "震"): (25, "天雷无妄"), ("艮", "乾"): (26, "山天大畜"),
    ("艮", "震"): (27, "山雷颐"), ("兑", "巽"): (28, "泽风大过"),
    ("坎", "坎"): (29, "坎为水"), ("离", "离"): (30, "离为火"),
    ("兑", "艮"): (31, "泽山咸"), ("震", "巽"): (32, "雷风恒"),
    ("乾", "艮"): (33, "天山遁"), ("震", "乾"): (34, "雷天大壮"),
    ("离", "坤"): (35, "火地晋"), ("坤", "离"): (36, "地火明夷"),
    ("巽", "离"): (37, "风火家人"), ("离", "兑"): (38, "火泽睽"),
    ("坎", "艮"): (39, "水山蹇"), ("震", "坎"): (40, "雷水解"),
    ("艮", "兑"): (41, "山泽损"), ("巽", "震"): (42, "风雷益"),
    ("兑", "乾"): (43, "泽天夬"), ("乾", "巽"): (44, "天风姤"),
    ("兑", "坤"): (45, "泽地萃"), ("坤", "巽"): (46, "地风升"),
    ("兑", "坎"): (47, "泽水困"), ("坎", "巽"): (48, "水风井"),
    ("兑", "离"): (49, "泽火革"), ("离", "巽"): (50, "火风鼎"),
    ("震", "震"): (51, "震为雷"), ("艮", "艮"): (52, "艮为山"),
    ("巽", "艮"): (53, "风山渐"), ("震", "兑"): (54, "雷泽归妹"),
    ("震", "离"): (55, "雷火丰"), ("离", "艮"): (56, "火山旅"),
    ("巽", "巽"): (57, "巽为风"), ("兑", "兑"): (58, "兑为泽"),
    ("巽", "坎"): (59, "风水涣"), ("坎", "兑"): (60, "水泽节"),
    ("巽", "兑"): (61, "风泽中孚"), ("震", "艮"): (62, "雷山小过"),
    ("坎", "离"): (63, "水火既济"), ("离", "坎"): (64, "火水未济"),
}

NAME_TO_KEY = {name: key for key, (seq, name) in HEXAGRAMS.items()}


def hex_from_trigrams(upper_name: str, lower_name: str) -> dict:
    seq, title = HEXAGRAMS[(upper_name, lower_name)]
    binary = TRIGRAM[lower_name] + TRIGRAM[upper_name]
    return {
        "sequence": seq,
        "name": title,
        "binary": binary,
        "上卦": upper_name,
        "下卦": lower_name,
    }


def hugua_from_binary(binary: str) -> dict:
    """互卦：下互=二三四爻，上互=三四五爻（binary 初→上）。"""
    lower_hu = BITS_TRIGRAM[binary[1:4]]
    upper_hu = BITS_TRIGRAM[binary[2:5]]
    info = hex_from_trigrams(upper_hu, lower_hu)
    return {
        "sequence": info["sequence"],
        "name": info["name"],
        "binary": info["binary"],
        "下互": lower_hu,
        "上互": upper_hu,
    }


def coin_values_to_binary(values: list[int]) -> str:
    """铜钱六爻值 6/7/8/9（初→上）→ 本卦 binary。"""
    bits = []
    for v in values:
        if v in (7, 9):
            bits.append("1")
        elif v in (6, 8):
            bits.append("0")
        else:
            raise ValueError(f"无效爻值: {v}，应为 6/7/8/9")
    return "".join(bits)


def moving_from_values(values: list[int]) -> list[int]:
    return [i + 1 for i, v in enumerate(values) if v in (6, 9)]


def hex_from_coin_values(values: list[int]) -> dict:
    if len(values) != 6:
        raise ValueError("铜钱法须 6 个爻值")
    binary = coin_values_to_binary(values)
    upper = BITS_TRIGRAM[binary[3:]]
    lower = BITS_TRIGRAM[binary[:3]]
    moving = moving_from_values(values)
    ben = hex_from_trigrams(upper, lower)
    bian = None
    if moving:
        bits = list(binary)
        for m in moving:
            bits[m - 1] = "0" if bits[m - 1] == "1" else "1"
        cb = "".join(bits)
        bian = hex_from_trigrams(BITS_TRIGRAM[cb[3:]], BITS_TRIGRAM[cb[:3]])
    return {
        "本卦": ben,
        "变卦": bian,
        "互卦": hugua_from_binary(binary),
        "动爻": moving,
        "binary": binary,
    }


def trigram_from_remainder(n: int) -> str:
    r = n % 8
    return {0: "坤", 1: "乾", 2: "兑", 3: "离", 4: "震", 5: "巽", 6: "坎", 7: "艮"}[r]


def digital_cast(nums: tuple[int, int, int]) -> dict:
    """数字法（本 skill 取法）：第一数→下卦，第二数→上卦，第三数→动爻。"""
    if len(nums) != 3:
        raise ValueError("数字法须三个数")
    n1, n2, n3 = nums
    lower = trigram_from_remainder(n1)
    upper = trigram_from_remainder(n2)
    moving = 6 if n3 % 6 == 0 else n3 % 6
    ben = hex_from_trigrams(upper, lower)
    binary = ben["binary"]
    bits = list(binary)
    bits[moving - 1] = "0" if bits[moving - 1] == "1" else "1"
    cb = "".join(bits)
    bian = hex_from_trigrams(BITS_TRIGRAM[cb[3:]], BITS_TRIGRAM[cb[:3]])
    return {
        "本卦": ben,
        "变卦": bian,
        "互卦": hugua_from_binary(binary),
        "动爻": [moving],
        "binary": binary,
        "取数": {"下卦数": n1, "上卦数": n2, "动爻数": n3},
    }


def ti_yong_from_moving(moving: list[int], binary: str) -> dict:
    """铜钱/数字法体用：上下经卦动爻计数定体用。"""
    lower_bits, upper_bits = binary[:3], binary[3:]
    lower_m = sum(1 for m in moving if m <= 3)
    upper_m = sum(1 for m in moving if m >= 4)
    lower_name = BITS_TRIGRAM[lower_bits]
    upper_name = BITS_TRIGRAM[upper_bits]
    if lower_m == 0 and upper_m == 0:
        ti, yong = upper_name, lower_name
    elif lower_m > 0 and upper_m == 0:
        ti, yong = upper_name, lower_name
    elif upper_m > 0 and lower_m == 0:
        ti, yong = lower_name, upper_name
    elif lower_m > upper_m:
        ti, yong = upper_name, lower_name
    elif upper_m > lower_m:
        ti, yong = lower_name, upper_name
    else:
        ti, yong = lower_name, upper_name
    wx_ti, wx_yong = WUXING[ti], WUXING[yong]
    shengke = {
        ("木", "火"): "体生用", ("火", "土"): "体生用", ("土", "金"): "体生用",
        ("金", "水"): "体生用", ("水", "木"): "体生用",
        ("火", "木"): "用生体", ("土", "火"): "用生体", ("金", "土"): "用生体",
        ("水", "金"): "用生体", ("木", "水"): "用生体",
        ("木", "土"): "体克用", ("土", "水"): "体克用", ("水", "火"): "体克用",
        ("火", "金"): "体克用", ("金", "木"): "体克用",
        ("土", "木"): "用克体", ("水", "土"): "用克体", ("火", "水"): "用克体",
        ("金", "火"): "用克体", ("木", "金"): "用克体",
    }
    rel = shengke.get((wx_ti, wx_yong), "体用比和" if wx_ti == wx_yong else "未知")
    return {
        "体卦": ti, "用卦": yong,
        "体五行": wx_ti, "用五行": wx_yong, "生克": rel,
        "下卦动数": lower_m, "上卦动数": upper_m,
    }
