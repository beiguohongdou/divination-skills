#!/usr/bin/env python3
"""
六爻纳甲装卦 —— 本卦名/序 + 动爻 + 日期 → 八宫、世应、纳甲、六亲、六神、旬空。

用法：
    py -3 liuyao_pan.py --hex 地雷复 --moving 6 --date 2026-07-04 --json
    py -3 liuyao_pan.py --seq 24 --moving 1,6 --json

依赖：同目录 ganzhi.py（无第三方库）
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 导入 ganzhi
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ganzhi import compute as ganzhi_compute, DIZHI, is_chong, TIANGAN

# 八宫卦序 → 世爻位（1-6）
SHI_BY_INDEX = [6, 1, 2, 3, 4, 5, 4, 3]

PALACE_HEX: dict[str, list[str]] = {
    "乾": ["乾为天", "天风姤", "天山遁", "天地否", "风地观", "山地剥", "火地晋", "火天大有"],
    "震": ["震为雷", "雷地豫", "雷水解", "雷风恒", "地风升", "水风井", "泽风大过", "泽雷随"],
    "坎": ["坎为水", "水泽节", "水雷屯", "水火既济", "泽火革", "雷火丰", "地火明夷", "地水师"],
    "艮": ["艮为山", "山火贲", "山天大畜", "山泽损", "火泽睽", "天泽履", "风泽中孚", "风山渐"],
    "坤": ["坤为地", "地雷复", "地泽临", "地天泰", "雷天大壮", "泽天夬", "水天需", "水地比"],
    "巽": ["巽为风", "风天小畜", "风火家人", "风雷益", "天雷无妄", "火雷噬嗑", "山雷颐", "山风蛊"],
    "离": ["离为火", "火山旅", "火风鼎", "火水未济", "山水蒙", "风水涣", "天水讼", "天火同人"],
    "兑": ["兑为泽", "泽水困", "泽地萃", "泽山咸", "水山蹇", "地山谦", "雷山小过", "雷泽归妹"],
}

PALACE_WX = {"乾": "金", "兑": "金", "离": "火", "震": "木", "巽": "木", "坎": "水", "艮": "土", "坤": "土"}

TRIGRAM = {
    "乾": "111", "兑": "110", "离": "101", "震": "100",
    "巽": "011", "坎": "010", "艮": "001", "坤": "000",
}
BITS_TRIGRAM = {v: k for k, v in TRIGRAM.items()}

NA_YANG = {
    "乾": ["子", "寅", "辰"], "震": ["子", "寅", "辰"],
    "坎": ["寅", "辰", "午"], "艮": ["辰", "午", "申"],
}
NA_YIN = {
    "坤": ["未", "巳", "卯"], "兑": ["巳", "卯", "丑"],
    "离": ["卯", "丑", "亥"], "巽": ["丑", "亥", "酉"],
}

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
SEQ_TO_NAME = {v[0]: v[1] for v in HEXAGRAMS.values()}

WX_DZ = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
         "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}

LIUSHEN_ROW = {
    "甲乙": ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"],
    "丙丁": ["朱雀", "勾陈", "螣蛇", "白虎", "玄武", "青龙"],
    "戊": ["勾陈", "螣蛇", "白虎", "玄武", "青龙", "朱雀"],
    "己": ["螣蛇", "白虎", "玄武", "青龙", "朱雀", "勾陈"],
    "庚辛": ["白虎", "玄武", "青龙", "朱雀", "勾陈", "螣蛇"],
    "壬癸": ["玄武", "青龙", "朱雀", "勾陈", "螣蛇", "白虎"],
}


def liuqin(palace_wx: str, branch_wx: str) -> str:
    if branch_wx == palace_wx:
        return "兄弟"
    sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    ke = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    if sheng[palace_wx] == branch_wx:
        return "子孙"
    if sheng[branch_wx] == palace_wx:
        return "父母"
    if ke[palace_wx] == branch_wx:
        return "妻财"
    if ke[branch_wx] == palace_wx:
        return "官鬼"
    return "?"


def najia_branches(lower: str, upper: str) -> list[str]:
    low = NA_YANG if lower in NA_YANG else NA_YIN
    up = NA_YANG if upper in NA_YANG else NA_YIN
    return low[lower] + up[upper]


def find_palace(name: str) -> tuple[str, int]:
    for palace, names in PALACE_HEX.items():
        if name in names:
            idx = names.index(name)
            return palace, SHI_BY_INDEX[idx]
    raise ValueError(f"未知卦名: {name}")


def ying_line(shi: int) -> int:
    return ((shi + 2) % 6) + 1


def liushen_for_day(tiangan: str) -> list[str]:
    if tiangan in ("甲", "乙"):
        return LIUSHEN_ROW["甲乙"]
    if tiangan in ("丙", "丁"):
        return LIUSHEN_ROW["丙丁"]
    if tiangan == "戊":
        return LIUSHEN_ROW["戊"]
    if tiangan == "己":
        return LIUSHEN_ROW["己"]
    if tiangan in ("庚", "辛"):
        return LIUSHEN_ROW["庚辛"]
    return LIUSHEN_ROW["壬癸"]


def parse_moving(s: str) -> list[int]:
    if not s:
        return []
    out = []
    for part in s.replace("，", ",").split(","):
        part = part.strip()
        if part:
            out.append(int(part))
    return sorted(set(out))


def fanyin_fuyin(branches: list[str], moving: list[int], changed_branches: list[str] | None) -> dict:
    if not moving or not changed_branches:
        return {"反吟爻": [], "伏吟爻": []}
    fan, fu = [], []
    for i in moving:
        j = i - 1
        if is_chong(branches[j], changed_branches[j]):
            fan.append(i)
        if branches[j] == changed_branches[j]:
            fu.append(i)
    return {"反吟爻": fan, "伏吟爻": fu}


def build_pan(hex_name: str, moving: list[int], d: date) -> dict:
    if hex_name not in NAME_TO_KEY:
        raise ValueError(f"无法识别卦名: {hex_name}")
    upper, lower = NAME_TO_KEY[hex_name]
    seq, _ = HEXAGRAMS[(upper, lower)]
    palace, shi = find_palace(hex_name)
    ying = ying_line(shi)
    branches = najia_branches(lower, upper)
    pwx = PALACE_WX[palace]
    gz = ganzhi_compute(d)

    bits = TRIGRAM[lower] + TRIGRAM[upper]
    lines = []
    liushen = liushen_for_day(gz["日天干"])
    yao_labels = ["初", "二", "三", "四", "五", "上"]
    for i in range(6):
        pos = i + 1
        dz = branches[i]
        is_yang = bits[i] == "1"
        yy = "九" if is_yang else "六"
        lines.append({
            "爻位": pos,
            "爻名": yao_labels[i] + yy,
            "地支": dz,
            "五行": WX_DZ[dz],
            "六亲": liuqin(pwx, WX_DZ[dz]),
            "六神": liushen[i],
            "世": pos == shi,
            "应": pos == ying,
            "动": pos in moving,
            "旬空": dz in gz["旬空"],
        })

    changed_branches = None
    if moving:
        bits = list(TRIGRAM[lower] + TRIGRAM[upper])
        for m in moving:
            bits[m - 1] = "0" if bits[m - 1] == "1" else "1"
        cb = "".join(bits)
        changed_branches = najia_branches(BITS_TRIGRAM[cb[:3]], BITS_TRIGRAM[cb[3:]])

    return {
        "本卦": {"序": seq, "名": hex_name, "上卦": upper, "下卦": lower},
        "八宫": palace,
        "本宫五行": pwx,
        "世爻": shi,
        "应爻": ying,
        "动爻": moving,
        "日干支": gz,
        "月建说明": gz.get("月建说明", "按节气近似日，交节当日可能有偏差"),
        "六爻": lines,
        "反吟伏吟": fanyin_fuyin(branches, moving, changed_branches),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="六爻纳甲装卦")
    p.add_argument("--hex", help="卦名，如 地雷复")
    p.add_argument("--seq", type=int, help="卦序 1-64")
    p.add_argument("--moving", default="", help="动爻位，逗号分隔，如 1,6")
    p.add_argument("--date", help="占日 YYYY-MM-DD，默认今天")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    if args.seq:
        hex_name = SEQ_TO_NAME.get(args.seq)
        if not hex_name:
            sys.exit(f"无效卦序: {args.seq}")
    elif args.hex:
        hex_name = args.hex
    else:
        sys.exit("请指定 --hex 或 --seq")

    d = date.fromisoformat(args.date) if args.date else date.today()
    moving = parse_moving(args.moving)
    result = build_pan(hex_name, moving, d)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"本卦: {result['本卦']['名']}  八宫:{result['八宫']}({result['本宫五行']})")
        print(f"世{result['世爻']} 应{result['应爻']}  动爻:{result['动爻'] or '无'}")
        print(f"日干支:{result['日干支']['日干支']} 旬空:{'、'.join(result['日干支']['旬空'])} 月建:{result['日干支']['月建']}")
        for ln in result["六爻"]:
            flags = []
            if ln["世"]:
                flags.append("世")
            if ln["应"]:
                flags.append("应")
            if ln["动"]:
                flags.append("动")
            if ln["旬空"]:
                flags.append("空")
            print(f"  {ln['爻名']} {ln['地支']} {ln['六亲']} {ln['六神']} {' '.join(flags)}")


if __name__ == "__main__":
    main()
