#!/usr/bin/env python3
"""
六爻纳甲装卦 —— 本卦名/序 + 动爻 + 日期 → 八宫、世应、纳甲、六亲、六神、旬空。

用法：
    py -3 liuyao_pan.py --hex 地雷复 --moving 6 --date 2026-07-04 --json
    py -3 liuyao_pan.py --seq 24 --moving 1,6 --json

依赖：同目录 ganzhi.py、jieqi.py（可选 ephem 精确月建）
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


def wangshuai(yao_wx: str, yue_wx: str) -> str:
    """月建对爻五行的旺相休囚死。"""
    if yao_wx == yue_wx:
        return "旺"
    sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    ke = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    if sheng[yue_wx] == yao_wx:
        return "相"
    if sheng[yao_wx] == yue_wx:
        return "休"
    if ke[yao_wx] == yue_wx:
        return "囚"
    if ke[yue_wx] == yao_wx:
        return "死"
    return "?"


def an_dong_ri_po(is_moving: bool, dz: str, day_dz: str, ws: str, in_xunkong: bool) -> str | None:
    """静爻被日冲 → 暗动（旺相）或日破（休囚死）；旬空被冲不作暗动。"""
    if is_moving or not is_chong(dz, day_dz):
        return None
    if in_xunkong:
        return "冲空"
    if ws in ("旺", "相"):
        return "暗动"
    return "日破"


def flip_hex_bits(hex_name: str, moving: list[int]) -> tuple[str, str]:
    upper, lower = NAME_TO_KEY[hex_name]
    bits = list(TRIGRAM[lower] + TRIGRAM[upper])
    for m in moving:
        bits[m - 1] = "0" if bits[m - 1] == "1" else "1"
    cb = "".join(bits)
    upper_t = BITS_TRIGRAM[cb[3:]]
    lower_t = BITS_TRIGRAM[cb[:3]]
    changed_name = HEXAGRAMS[(upper_t, lower_t)][1]
    return changed_name, cb


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


JIN = {("寅", "卯"), ("申", "酉"), ("丑", "辰"), ("未", "戌"), ("巳", "午"), ("亥", "子")}
TUI = {(b, a) for a, b in JIN}

REV_SHENG = {"火": "木", "土": "火", "金": "土", "水": "金", "木": "水"}

# 五行入墓（辰戌丑未四库）
WUXING_MU = {"木": "未", "火": "戌", "金": "丑", "水": "辰", "土": "辰"}

YUE_NUM = {dz: i + 1 for i, dz in enumerate(DIZHI)}


def in_mu(wx: str, dz: str) -> bool:
    return WUXING_MU.get(wx) == dz


def gua_shen_yao(shi_pos: int, shi_yang: bool, yue_jian: str) -> dict:
    """卦身爻位（《卜筮正宗》口诀简版：阳世从子数、阴世从午数至月建取爻位）。"""
    n = YUE_NUM[yue_jian]
    if shi_yang:
        pos = n % 6
    else:
        pos = (n + 6) % 6
    pos = 6 if pos == 0 else pos
    return {
        "爻位": pos,
        "世爻阴阳": "阳" if shi_yang else "阴",
        "月建": yue_jian,
        "说明": "阳世从子数至月建、阴世从午数至月建（简版爻位公式）",
    }

TOPIC_YONGSHEN: dict[str, tuple[str, str]] = {
    "求财": ("妻财", "占财以妻财为用神"),
    "求官": ("官鬼", "占官功名以官鬼为用神"),
    "功名": ("官鬼", "占官功名以官鬼为用神"),
    "婚姻": ("妻财", "男占妻财、女占官鬼（未指定性别时默认妻财，女命请改官鬼）"),
    "疾病": ("官鬼", "占病以官鬼为病神；占自身康复兼看世爻"),
    "出行": ("世爻", "占出行以世爻为用"),
    "子女": ("子孙", "占子女以子孙为用神"),
    "诉讼": ("官鬼", "占官司以官鬼为用神"),
    "赛事": ("世爻", "赛事世为一方、应为对方；进球象可看子孙"),
    "失物": ("妻财", "占失物以妻财为用神"),
    "房屋": ("父母", "占宅以父母为用神"),
    "文书": ("父母", "占文书以父母为用神"),
}

SHENG_WX = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE_WX = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def liuqin_to_wuxing(palace_wx: str, target_lq: str) -> str:
    """本宫五行下，某六亲对应的五行。"""
    for wx in ("木", "火", "土", "金", "水"):
        if liuqin(palace_wx, wx) == target_lq:
            return wx
    return "?"


def jin_tui_shen(old_dz: str, new_dz: str) -> str | None:
    if (old_dz, new_dz) in JIN:
        return "进神"
    if (old_dz, new_dz) in TUI:
        return "退神"
    return None


def compute_fushen(palace: str, pwx: str, lines: list[dict]) -> list[dict]:
    """卦中缺六亲时，查本宫纯卦得伏神。"""
    pure_name = PALACE_HEX[palace][0]
    pu, pl = NAME_TO_KEY[pure_name]
    pure_br = najia_branches(pl, pu)
    present = {ln["六亲"] for ln in lines}
    all_lq = {"父母", "兄弟", "子孙", "妻财", "官鬼"}
    out = []
    for lq in sorted(all_lq - present):
        for i, dz in enumerate(pure_br):
            if liuqin(pwx, WX_DZ[dz]) == lq:
                pos = i + 1
                fei = lines[i]
                out.append({
                    "六亲": lq,
                    "伏于爻位": pos,
                    "伏神地支": dz,
                    "伏神五行": WX_DZ[dz],
                    "飞神地支": fei["地支"],
                    "飞神六亲": fei["六亲"],
                    "飞神旺衰": fei.get("旺衰"),
                })
                break
    return out


def yongshen_analysis(
    topic: str | None,
    palace_wx: str,
    lines: list[dict],
    fushen: list[dict],
    shi: int,
    ying: int,
) -> dict:
    hint = "未指定问事类型；可参考世应或让用户说明（求财/婚姻/疾病等）"
    primary_lq = None
    if topic:
        key = topic.strip()
        for k, (lq, note) in TOPIC_YONGSHEN.items():
            if k in key or key in k:
                primary_lq, hint = lq, note
                break

    def find_lines(lq: str) -> list[dict]:
        if lq == "世爻":
            return [ln for ln in lines if ln["爻位"] == shi]
        if lq == "应爻":
            return [ln for ln in lines if ln["爻位"] == ying]
        return [ln for ln in lines if ln["六亲"] == lq]

    yong_lines = find_lines(primary_lq) if primary_lq else []
    yong_fushen = [f for f in fushen if primary_lq and f["六亲"] == primary_lq] if primary_lq else []

    yuan, ji, chou = None, None, None
    if primary_lq and primary_lq not in ("世爻", "应爻"):
        ywx = liuqin_to_wuxing(palace_wx, primary_lq)
        yuan_wx = REV_SHENG.get(ywx, "?")
        ji_wx = KE_WX.get(ywx, "?")
        yuan_lq = liuqin(palace_wx, yuan_wx) if yuan_wx != "?" else "?"
        ji_lq = liuqin(palace_wx, ji_wx) if ji_wx != "?" else "?"
        yuan = {"六亲": yuan_lq, "爻位": [ln["爻位"] for ln in lines if ln["六亲"] == yuan_lq]}
        ji = {"六亲": ji_lq, "爻位": [ln["爻位"] for ln in lines if ln["六亲"] == ji_lq]}
        if yuan_lq != "?":
            cw = KE_WX.get(yuan_wx, "?")
            clq = liuqin(palace_wx, cw) if cw != "?" else "?"
            chou = {"六亲": clq, "爻位": [ln["爻位"] for ln in lines if ln["六亲"] == clq], "说明": "克原神者为仇"}
        elif ji_lq != "?":
            jwx = liuqin_to_wuxing(palace_wx, ji_lq)
            sw = REV_SHENG.get(jwx, "?")
            slq = liuqin(palace_wx, sw) if sw != "?" else "?"
            chou = {"六亲": slq, "爻位": [ln["爻位"] for ln in lines if ln["六亲"] == slq], "说明": "生忌神者为仇"}

    return {
        "问事": topic or "未指定",
        "用神": primary_lq,
        "说明": hint,
        "用神爻": [{"爻位": ln["爻位"], "地支": ln["地支"], "旺衰": ln.get("旺衰"), "动": ln["动"]} for ln in yong_lines],
        "用神伏神": yong_fushen,
        "原神": yuan,
        "忌神": ji,
        "仇神": chou,
    }


def build_pan(hex_name: str, moving: list[int], d: date, topic: str | None = None) -> dict:
    if hex_name not in NAME_TO_KEY:
        raise ValueError(f"无法识别卦名: {hex_name}")
    upper, lower = NAME_TO_KEY[hex_name]
    seq, _ = HEXAGRAMS[(upper, lower)]
    palace, shi = find_palace(hex_name)
    ying = ying_line(shi)
    branches = najia_branches(lower, upper)
    pwx = PALACE_WX[palace]
    gz = ganzhi_compute(d)
    yue_wx = WX_DZ[gz["月建"]]
    yue_jian = gz["月建"]
    day_dz = gz["日地支"]
    xunkong = set(gz["旬空"])

    bits = TRIGRAM[lower] + TRIGRAM[upper]
    changed_branches = None
    changed_section = None
    if moving:
        changed_name, changed_bits = flip_hex_bits(hex_name, moving)
        changed_branches = najia_branches(
            BITS_TRIGRAM[changed_bits[:3]], BITS_TRIGRAM[changed_bits[3:]]
        )
        c_upper, c_lower = NAME_TO_KEY[changed_name]
        c_palace, _ = find_palace(changed_name)
        c_pwx = PALACE_WX[c_palace]
        c_seq = HEXAGRAMS[(c_upper, c_lower)][0]
        changed_lines = []
        for i in range(6):
            pos = i + 1
            dz = changed_branches[i]
            wx = WX_DZ[dz]
            old_dz = branches[i]
            c_wx = WX_DZ[dz]
            changed_lines.append({
                "爻位": pos,
                "地支": dz,
                "五行": c_wx,
                "六亲": liuqin(c_pwx, c_wx),
                "动": pos in moving,
                "进退": jin_tui_shen(old_dz, dz) if pos in moving else None,
                "化空": dz in xunkong if pos in moving else False,
                "化墓": in_mu(c_wx, dz) if pos in moving else False,
            })
        changed_section = {
            "序": c_seq,
            "名": changed_name,
            "八宫": c_palace,
            "本宫五行": c_pwx,
            "六爻": changed_lines,
        }

    lines = []
    liushen = liushen_for_day(gz["日天干"])
    yao_labels = ["初", "二", "三", "四", "五", "上"]
    for i in range(6):
        pos = i + 1
        dz = branches[i]
        is_yang = bits[i] == "1"
        yy = "九" if is_yang else "六"
        wx = WX_DZ[dz]
        ws = wangshuai(wx, yue_wx)
        in_xk = dz in gz["旬空"]
        is_mov = pos in moving
        adrp = an_dong_ri_po(is_mov, dz, day_dz, ws, in_xk)
        jt = None
        if is_mov and changed_branches:
            jt = jin_tui_shen(dz, changed_branches[i])
        cdz = changed_branches[i] if changed_branches else None
        lines.append({
            "爻位": pos,
            "爻名": yao_labels[i] + yy,
            "地支": dz,
            "五行": wx,
            "六亲": liuqin(pwx, wx),
            "六神": liushen[i],
            "旺衰": ws,
            "世": pos == shi,
            "应": pos == ying,
            "动": is_mov,
            "旬空": in_xk,
            "月破": is_chong(dz, yue_jian),
            "入墓": in_mu(wx, dz),
            "日冲": is_chong(dz, day_dz),
            "暗动日破": adrp,
            "进退": jt,
            "化空": bool(is_mov and cdz and cdz in xunkong),
            "化墓": bool(is_mov and cdz and in_mu(WX_DZ[cdz], cdz)),
        })

    shi_yang = bits[shi - 1] == "1"
    gs = gua_shen_yao(shi, shi_yang, yue_jian)
    gs_line = next((ln for ln in lines if ln["爻位"] == gs["爻位"]), None)
    gs["地支"] = gs_line["地支"] if gs_line else None
    gs["六亲"] = gs_line["六亲"] if gs_line else None

    fushen = compute_fushen(palace, pwx, lines)
    yong = yongshen_analysis(topic, pwx, lines, fushen, shi, ying)
    jin_tui_list = [
        {"爻位": ln["爻位"], "化进退": ln["进退"]}
        for ln in lines if ln.get("进退")
    ]

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
        "变卦": changed_section,
        "反吟伏吟": fanyin_fuyin(branches, moving, changed_branches),
        "伏神": fushen,
        "进退神": jin_tui_list,
        "卦身": gs,
        "用神提示": yong,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="六爻纳甲装卦")
    p.add_argument("--hex", help="卦名，如 地雷复")
    p.add_argument("--seq", type=int, help="卦序 1-64")
    p.add_argument("--moving", default="", help="动爻位，逗号分隔，如 1,6")
    p.add_argument("--date", help="占日 YYYY-MM-DD，默认今天")
    p.add_argument("--topic", help="问事类型：求财/婚姻/疾病/赛事等，用于用神提示")
    p.add_argument("--json", action="store_true")
    p.add_argument("--question", "-q", default="", help="问事（写入日志）")
    p.add_argument("--log-id", help="追加到已有日志目录（写 liuyao_pan.json）；不传则新建目录")
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
    result = build_pan(hex_name, moving, d, topic=args.topic)

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    try:
        from _log_hook import attach_session_log, inject_log_into_result  # noqa: E402

        dt_str = str(d)
        if args.log_id:
            log_info = attach_session_log(
                system="yijing",
                method="liuyao_pan",
                payload=result,
                datetime_str=dt_str,
                question=args.question,
                script="liuyao_pan.py",
                log_id=args.log_id,
                extra_filename="liuyao_pan.json",
            )
        else:
            log_info = attach_session_log(
                system="yijing",
                method="liuyao_pan",
                payload=result,
                datetime_str=dt_str,
                question=args.question,
                script="liuyao_pan.py",
            )
        result = inject_log_into_result(result, log_info)
    except Exception:
        pass

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
            if ln.get("暗动日破"):
                flags.append(ln["暗动日破"])
            if ln.get("月破"):
                flags.append("月破")
            if ln.get("入墓"):
                flags.append("入墓")
            print(f"  {ln['爻名']} {ln['地支']} {ln['六亲']} {ln['六神']} {ln['旺衰']} {' '.join(flags)}")
        if result.get("卦身"):
            gs = result["卦身"]
            print(f"卦身: {gs.get('说明', '')} → {gs.get('爻位', '?')}爻")
        if result.get("变卦"):
            bg = result["变卦"]
            print(f"变卦: {bg['名']}  八宫:{bg['八宫']}")
        if result.get("伏神"):
            print("伏神:", "；".join(f"{f['六亲']}伏于{f['伏于爻位']}爻({f['伏神地支']})" for f in result["伏神"]) or "无")
        if result.get("进退神"):
            print("进退:", " ".join(f"{x['爻位']}爻{x['化进退']}" for x in result["进退神"]))
        ys = result.get("用神提示", {})
        if ys.get("用神"):
            print(f"用神提示: {ys['用神']} — {ys['说明']}")
            if ys.get("原神"):
                print(f"  原神: {ys['原神']['六亲']} @ {ys['原神']['爻位']}")
            if ys.get("忌神"):
                print(f"  忌神: {ys['忌神']['六亲']} @ {ys['忌神']['爻位']}")
            if ys.get("仇神"):
                print(f"  仇神: {ys['仇神']['六亲']} @ {ys['仇神']['爻位']} ({ys['仇神'].get('说明', '')})")
        if result.get("_session_log"):
            lg = result["_session_log"]
            print(f"[日志] id={lg['id']}  dir={lg['dir']}")


if __name__ == "__main__":
    main()
