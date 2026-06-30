#!/usr/bin/env python3
"""
梅花易数 · 年月日时起卦 —— 按公历/本地时间自动换算农历，输出本卦、变卦、动爻。

禁止 Agent 心算或背固定年数；必须运行本脚本（或同等逻辑）。

用法：
    python meihua_time.py                           # 当前时刻
    python meihua_time.py 2026-07-04 06:00        # 指定日期时间
    python meihua_time.py --datetime "2026-07-04 06:00" --json

依赖：
    pip install zhdate

算法（与 references/meihua-qigua.md 一致）：
    年数 = 农历年地支序数（子1 … 亥12），随农历年自动变化，禁止用公历年份数字
    月数 = 农历月（正月1 … 腊月12，闰月同月序）
    日数 = 农历日（初一1 … 三十30）
    时数 = 时辰地支序数（子1 … 亥12）
    上卦 = (年+月+日) mod 8，余0→坤(8)
    下卦 = (年+月+日+时) mod 8，余0→坤(8)
    动爻 = (年+月+日+时) mod 6，余0→上爻(6)
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

try:
    from zhdate import ZhDate
except ImportError:
    ZhDate = None  # type: ignore

DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 梅花卦数：余0→坤8
TRIGRAM = {
    0: ("坤", "☷", "000", 8),
    1: ("乾", "☰", "111", 1),
    2: ("兑", "☱", "110", 2),
    3: ("离", "☲", "101", 3),
    4: ("震", "☳", "100", 4),
    5: ("巽", "☴", "011", 5),
    6: ("坎", "☵", "010", 6),
    7: ("艮", "☶", "001", 7),
}

WUXING = {"乾": "金", "兑": "金", "离": "火", "震": "木", "巽": "木", "坎": "水", "艮": "土", "坤": "土"}

# (上卦名, 下卦名) -> (卦序, 卦名)
HEXAGRAMS: dict[tuple[str, str], tuple[int, str]] = {
    ("乾", "乾"): (1, "乾为天"),
    ("坤", "坤"): (2, "坤为地"),
    ("坎", "震"): (3, "水雷屯"),
    ("艮", "坎"): (4, "山水蒙"),
    ("坎", "乾"): (5, "水天需"),
    ("乾", "坎"): (6, "天水讼"),
    ("坤", "坎"): (7, "地水师"),
    ("坎", "坤"): (8, "水地比"),
    ("巽", "乾"): (9, "风天小畜"),
    ("乾", "兑"): (10, "天泽履"),
    ("坤", "乾"): (11, "地天泰"),
    ("乾", "坤"): (12, "天地否"),
    ("乾", "离"): (13, "天火同人"),
    ("离", "乾"): (14, "火天大有"),
    ("坤", "艮"): (15, "地山谦"),
    ("震", "坤"): (16, "雷地豫"),
    ("兑", "震"): (17, "泽雷随"),
    ("艮", "巽"): (18, "山风蛊"),
    ("坤", "兑"): (19, "地泽临"),
    ("巽", "坤"): (20, "风地观"),
    ("离", "震"): (21, "火雷噬嗑"),
    ("艮", "离"): (22, "山火贲"),
    ("艮", "坤"): (23, "山地剥"),
    ("坤", "震"): (24, "地雷复"),
    ("乾", "震"): (25, "天雷无妄"),
    ("艮", "乾"): (26, "山天大畜"),
    ("艮", "震"): (27, "山雷颐"),
    ("兑", "巽"): (28, "泽风大过"),
    ("坎", "坎"): (29, "坎为水"),
    ("离", "离"): (30, "离为火"),
    ("兑", "艮"): (31, "泽山咸"),
    ("震", "巽"): (32, "雷风恒"),
    ("乾", "艮"): (33, "天山遁"),
    ("震", "乾"): (34, "雷天大壮"),
    ("离", "坤"): (35, "火地晋"),
    ("坤", "离"): (36, "地火明夷"),
    ("巽", "离"): (37, "风火家人"),
    ("离", "兑"): (38, "火泽睽"),
    ("坎", "艮"): (39, "水山蹇"),
    ("震", "坎"): (40, "雷水解"),
    ("艮", "兑"): (41, "山泽损"),
    ("巽", "震"): (42, "风雷益"),
    ("兑", "乾"): (43, "泽天夬"),
    ("乾", "巽"): (44, "天风姤"),
    ("兑", "坤"): (45, "泽地萃"),
    ("坤", "巽"): (46, "地风升"),
    ("兑", "坎"): (47, "泽水困"),
    ("坎", "巽"): (48, "水风井"),
    ("兑", "离"): (49, "泽火革"),
    ("离", "巽"): (50, "火风鼎"),
    ("震", "震"): (51, "震为雷"),
    ("艮", "艮"): (52, "艮为山"),
    ("巽", "艮"): (53, "风山渐"),
    ("震", "兑"): (54, "雷泽归妹"),
    ("震", "离"): (55, "雷火丰"),
    ("离", "艮"): (56, "火山旅"),
    ("巽", "巽"): (57, "巽为风"),
    ("兑", "兑"): (58, "兑为泽"),
    ("巽", "坎"): (59, "风水涣"),
    ("坎", "兑"): (60, "水泽节"),
    ("巽", "兑"): (61, "风泽中孚"),
    ("震", "艮"): (62, "雷山小过"),
    ("坎", "离"): (63, "水火既济"),
    ("离", "坎"): (64, "火水未济"),
}

YAO_NAMES = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]


def mod8(n: int) -> int:
    r = n % 8
    return 8 if r == 0 else r


def mod6_line(n: int) -> int:
    r = n % 6
    return 6 if r == 0 else r


def lunar_year_dizhi_index(lunar_year: int) -> int:
    """农历年地支 0-based（子=0）。"""
    return (lunar_year - 4) % 12


def year_number(lunar_year: int) -> int:
    """年数：子1 … 亥12。"""
    return lunar_year_dizhi_index(lunar_year) + 1


def year_ganzhi(lunar_year: int) -> str:
    tg = TIANGAN[(lunar_year - 4) % 10]
    dz = DIZHI[lunar_year_dizhi_index(lunar_year)]
    return f"{tg}{dz}"


def shichen_from_clock(hour: int, minute: int = 0) -> tuple[str, int]:
    """公历时刻 → (时辰名, 时数1-12)。"""
    if hour == 23 or hour == 0:
        return "子", 1
    num = (hour + 1) // 2 + 1
    num = max(2, min(12, num))
    return DIZHI[num - 1], num


def parse_datetime(text: str) -> datetime:
    text = text.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析时间: {text!r}，请用 2026-07-04 06:00 格式")


def lunar_day_label(day: int) -> str:
    names = [
        "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
        "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
        "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十",
    ]
    if 1 <= day <= 30:
        return names[day - 1]
    return str(day)


def trigram_from_mod(remainder_mod8: int) -> dict:
    r = remainder_mod8 % 8
    name, sym, bits, num = TRIGRAM[r]
    return {"name": name, "symbol": sym, "bits": bits, "number": num}


def hexagram_info(upper: dict, lower: dict) -> dict:
    seq, title = HEXAGRAMS[(upper["name"], lower["name"])]
    binary = lower["bits"] + upper["bits"]
    return {"sequence": seq, "name": title, "binary": binary}


def hugua_from_binary(binary: str) -> dict:
    """互卦：下互=二三四爻，上互=三四五爻（初爻 index 0）。"""
    bit3_map = {"111": 1, "110": 2, "101": 3, "100": 4, "011": 5, "010": 6, "001": 7, "000": 0}
    lower_hu = trigram_from_mod(bit3_map[binary[1:4]])
    upper_hu = trigram_from_mod(bit3_map[binary[2:5]])
    info = hexagram_info(upper_hu, lower_hu)
    return {
        "sequence": info["sequence"],
        "name": info["name"],
        "binary": info["binary"],
        "下互": lower_hu["name"],
        "上互": upper_hu["name"],
    }


def flip_line(bits: str, line_index: int) -> str:
    """line_index 0=初爻 … 5=上爻"""
    chars = list(bits)
    chars[line_index] = "0" if chars[line_index] == "1" else "1"
    return "".join(chars)


def bits_to_trigrams(binary: str) -> tuple[dict, dict]:
    bit3_map = {"111": 1, "110": 2, "101": 3, "100": 4, "011": 5, "010": 6, "001": 7, "000": 0}
    upper = trigram_from_mod(bit3_map[binary[3:]])
    lower = trigram_from_mod(bit3_map[binary[:3]])
    return upper, lower


def ti_yong(moving_line: int, upper: dict, lower: dict) -> dict:
    """动爻所在经卦为用，另一为体。"""
    if moving_line <= 3:
        ti, yong = upper, lower
        ti_role, yong_role = "上卦", "下卦"
    else:
        ti, yong = lower, upper
        ti_role, yong_role = "下卦", "上卦"
    wx_ti, wx_yong = WUXING[ti["name"]], WUXING[yong["name"]]
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
        "体卦": ti["name"],
        "体卦位": ti_role,
        "用卦": yong["name"],
        "用卦位": yong_role,
        "体五行": wx_ti,
        "用五行": wx_yong,
        "生克": rel,
    }


def render_lines(binary: str, moving_line: int | None) -> str:
    rows = []
    for i in range(5, -1, -1):
        yang = binary[i] == "1"
        bar = "━━━" if yang else "━ ━"
        mark = " ○动" if moving_line == i + 1 else ""
        rows.append(f"{YAO_NAMES[i]}  {bar}  {'阳' if yang else '阴'}{mark}")
    return "\n".join(rows)


def compute(dt: datetime) -> dict:
    if ZhDate is None:
        raise RuntimeError("缺少依赖 zhdate，请运行: pip install zhdate")

    lunar = ZhDate.from_datetime(dt)
    ly, lm, ld = lunar.lunar_year, lunar.lunar_month, lunar.lunar_day
    yn, mn, dn = year_number(ly), lm, ld
    sc_name, hn = shichen_from_clock(dt.hour, dt.minute)

    sum3 = yn + mn + dn
    sum4 = sum3 + hn
    upper_mod = sum3 % 8
    lower_mod = sum4 % 8
    moving = mod6_line(sum4)

    upper = trigram_from_mod(upper_mod)
    lower = trigram_from_mod(lower_mod)
    ben = hexagram_info(upper, lower)

    changed_bits = flip_line(ben["binary"], moving - 1)
    upper_b, lower_b = bits_to_trigrams(changed_bits)
    bian = hexagram_info(upper_b, lower_b)
    hu = hugua_from_binary(ben["binary"])

    leap_note = "（闰月）" if getattr(lunar, "leap_month", False) else ""

    return {
        "输入": {
            "公历": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "农历": f"{year_ganzhi(ly)}年{lm}月{lunar_day_label(ld)}{leap_note} {sc_name}时",
        },
        "取数": {
            "年数": {"值": yn, "说明": f"农历{year_ganzhi(ly)}年 → {DIZHI[yn-1]} → {yn}（非公历{dt.year}）"},
            "月数": {"值": mn, "说明": f"农历{lm}月"},
            "日数": {"值": dn, "说明": f"农历{lunar_day_label(ld)}"},
            "时数": {"值": hn, "说明": f"{dt.strftime('%H:%M')} → {sc_name}时 → {hn}"},
        },
        "计算": {
            "年+月+日": sum3,
            "年+月+日+时": sum4,
            "上卦余数": upper_mod,
            "下卦余数": lower_mod,
            "动爻余数": sum4 % 6,
            "公式": "上卦=(年+月+日)÷8余数；下卦=(年+月+日+时)÷8余数；动爻=(年+月+日+时)÷6余数(0=上爻)",
        },
        "上卦": upper,
        "下卦": lower,
        "动爻": moving,
        "动爻名": YAO_NAMES[moving - 1],
        "本卦": ben,
        "变卦": bian,
        "互卦": hu,
        "体用": ti_yong(moving, upper, lower),
        "卦象": render_lines(ben["binary"], moving),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="梅花易数年月日时起卦")
    parser.add_argument("datetime_pos", nargs="?", help="如 2026-07-04 06:00")
    parser.add_argument("time_pos", nargs="?", help="可选时间部分")
    parser.add_argument("--datetime", "-d", help="完整日期时间字符串")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--question", "-q", default="", help="问事（写入日志 meta）")
    parser.add_argument("--log-id", help="追加到已有日志目录（如 liuyao 链式调用）")
    args = parser.parse_args()

    if args.datetime:
        dt = parse_datetime(args.datetime)
    elif args.datetime_pos:
        combined = args.datetime_pos if not args.time_pos else f"{args.datetime_pos} {args.time_pos}"
        dt = parse_datetime(combined)
    else:
        dt = datetime.now()

    try:
        result = compute(dt)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    try:
        from _log_hook import attach_session_log, inject_log_into_result  # noqa: E402

        log_info = attach_session_log(
            system="yijing",
            method="meihua_time",
            payload=result,
            datetime_str=result["输入"]["公历"],
            question=args.question,
            script="meihua_time.py",
            log_id=args.log_id,
        )
        result = inject_log_into_result(result, log_info)
    except Exception:
        pass

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        inp = result["输入"]
        q = result["取数"]
        print(f"公历: {inp['公历']}")
        print(f"农历: {inp['农历']}")
        print()
        print("取数（随农历年自动变化，禁止背固定年数）:")
        for k in ("年数", "月数", "日数", "时数"):
            item = q[k]
            print(f"  {k}: {item['值']}  ← {item['说明']}")
        calc = result["计算"]
        print()
        print(f"计算: {calc['年+月+日']} → 上卦余{calc['上卦余数']}；+时={calc['年+月+日+时']} → 下卦余{calc['下卦余数']}，动爻余{calc['动爻余数']}")
        print()
        ben, bian = result["本卦"], result["变卦"]
        hu = result["互卦"]
        print(f"本卦: {ben['name']}（{ben['binary']}）")
        print(f"变卦: {bian['name']}（{bian['binary']}）")
        print(f"互卦: {hu['name']}（下互{hu['下互']} 上互{hu['上互']}）")
        print(f"动爻: {result['动爻名']}")
        ty = result["体用"]
        print(f"体用: 体{ty['体卦']}({ty['体五行']}) 用{ty['用卦']}({ty['用五行']}) → {ty['生克']}")
        print()
        print(result["卦象"])
        if result.get("_session_log"):
            print(f"\n[日志] id={result['_session_log']['id']}  dir={result['_session_log']['dir']}")


if __name__ == "__main__":
    main()
