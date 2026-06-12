#!/usr/bin/env python3
"""
奇门遁甲排盘工具 —— 输入公历日期和时间，输出九宫格局（地盘、天盘、八门、九星、八神）。

用法：
    python qimen.py                             # 使用当前日期和时间
    python qimen.py 2026-05-22 14:00            # 指定日期和时间
    python qimen.py --json 2026-05-22 14:00     # JSON 输出

依赖：
    本脚本需与 ganzhi.py 放在同一目录，或已安装至 Python path。
"""

import sys
import os
import json
from datetime import date, datetime

# 确保能找到 ganzhi.py
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_THIS_DIR)
_SIBLING_DIR = os.path.join(os.path.dirname(_PARENT_DIR), "yijing-divination", "scripts")
sys.path.insert(0, _SIBLING_DIR)

from ganzhi import (
    TIANGAN, DIZHI, GANZHI_60, WUXING_DZ, WUXING_TG,
    get_day_ganzhi, get_ganzhi_index, get_yuejian,
    compute as ganzhi_compute,
)

# ──────────────────────────────────────────────
# 常量定义
# ──────────────────────────────────────────────

# 九宫: 坎1/坤2/震3/巽4/中5/乾6/兑7/艮8/离9
# 中5寄坤2

# 九星 (按宫位顺序1-9，中5寄2)
JIUXING = ["天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"]

# 九星原始宫位
JIUXING_GONG = {star: i + 1 for i, star in enumerate(JIUXING)}

# 八门 (按宫位顺序1-9, 中5无门)
BAMEN = ["休", "死", "伤", "杜", "", "开", "惊", "生", "景"]
BAMEN_GONG = {BAMEN[i]: i + 1 for i in range(9) if BAMEN[i]}

# 八神 (阳遁/阴遁)
BASHEN_YANG = ["值符", "螣蛇", "太阴", "六合", "勾陈", "朱雀", "九地", "九天"]
BASHEN_YIN  = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]

# 三奇六仪
LIUYI   = "戊己庚辛壬癸"  # 六仪
SANQI   = "丁丙乙"          # 三奇
QILI_YUAN = "戊己庚辛壬癸丁丙乙"  # 全序

# 六仪对应的旬首
LIUYI_XUNSHOU = {"戊": "甲子", "己": "甲戌", "庚": "甲申", "辛": "甲午", "壬": "甲辰", "癸": "甲寅"}

# 时节气表: (月,日,节气名,阳遁局数(上中下),阴遁局数(上中下))
# 阳遁: 冬至→芒种; 阴遁: 夏至→大雪
# 格式: (月,日,节气名,上元局,中元局,下元局, 阳0/阴1)
JIEQI = [
    ( 1,  6, "小寒",  2, 8, 5, 0),   # 阳遁
    ( 1, 21, "大寒",  3, 9, 6, 0),
    ( 2,  4, "立春",  8, 5, 2, 0),
    ( 2, 19, "雨水",  9, 6, 3, 0),
    ( 3,  6, "惊蛰",  1, 7, 4, 0),
    ( 3, 21, "春分",  3, 9, 6, 0),
    ( 4,  5, "清明",  4, 1, 7, 0),
    ( 4, 21, "谷雨",  5, 2, 8, 0),
    ( 5,  6, "立夏",  4, 1, 7, 0),
    ( 5, 22, "小满",  5, 2, 8, 0),
    ( 6,  6, "芒种",  6, 3, 9, 0),
    ( 6, 22, "夏至",  9, 3, 6, 1),   # 阴遁
    ( 7,  7, "小暑",  8, 2, 5, 1),
    ( 7, 23, "大暑",  7, 1, 4, 1),
    ( 8,  7, "立秋",  2, 5, 8, 1),
    ( 8, 24, "处暑",  1, 4, 7, 1),
    ( 9,  8, "白露",  9, 3, 6, 1),
    ( 9, 23, "秋分",  7, 1, 4, 1),
    (10,  8, "寒露",  6, 9, 3, 1),
    (10, 24, "霜降",  5, 8, 2, 1),
    (11,  7, "立冬",  6, 9, 3, 1),
    (11, 23, "小雪",  5, 8, 2, 1),
    (12,  7, "大雪",  4, 7, 1, 1),
    (12, 22, "冬至",  1, 7, 4, 0),   # 阳遁
]

# 时辰地支
SHI_ZHI = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# ──────────────────────────────────────────────
# 运算函数
# ──────────────────────────────────────────────

def get_jieqi(d: date):
    """根据日期返回节气信息 (节气名, 阴阳遁, 上中下三元局数)"""
    for m, day, name, ju1, ju2, ju3, yinyang in reversed(JIEQI):
        if d.month > m or (d.month == m and d.day >= day):
            return name, "阴遁" if yinyang else "阳遁", (ju1, ju2, ju3)
    return "冬至", "阳遁", (1, 7, 4)

def get_sanyuan(gz_index: int):
    """
    确定三元(上/中/下)。
    基于日干支所在旬的旬首地支:
    子午卯酉 → 上元, 寅申巳亥 → 中元, 辰戌丑未 → 下元
    """
    xun = gz_index // 10  # 旬号 0-5
    xunshou_idx = xun * 10  # 旬首在60干支表的索引
    xunshou_dz = GANZHI_60[xunshou_idx][1]  # 取地支
    if xunshou_dz in "子午卯酉":
        return 0  # 上元
    elif xunshou_dz in "寅申巳亥":
        return 1  # 中元
    else:
        return 2  # 下元

def get_shichen_index(hour: int) -> int:
    """小时 → 时辰地支索引"""
    return ((hour + 1) // 2) % 12 if hour != 23 else 0

def build_dipan(ju: int, yinyang: str) -> dict:
    """
    建地盘。阳遁顺排六仪逆排三奇，阴遁逆排三奇顺排六仪。
    戊在局数宫，阳顺阴逆。
    返回: {宫号1-9: 天干}
    """
    pan = {}
    order = list(range(1, 10))  # 1-9
    # 阳遁顺: 戊己庚辛壬癸丁丙乙
    # 阴遁逆: 戊己庚辛壬癸丁丙乙 (但方向相反)
    for i, gan in enumerate(QILI_YUAN):
        if yinyang == "阳遁":
            gong = (ju - 1 + i) % 9 + 1  # 从ju宫开始顺排
        else:
            gong = (ju - 1 - i) % 9 + 1  # 从ju宫开始逆排
        pan[gong] = gan
    return pan

def find_gong_with_gan(pan: dict, gan: str) -> int:
    """找某个天干所在的宫"""
    for gong in range(1, 10):
        if pan.get(gong) == gan:
            return gong
    return 5  # 默认中宫

def build_qimen(dt: datetime) -> dict:
    """排一局完整的奇门盘"""
    d = dt.date()
    h = dt.hour

    # 干支基础
    gz_info = ganzhi_compute(d)
    rigan = gz_info["日天干"]
    rizhi = gz_info["日地支"]
    gz_idx = gz_info["干支序数"] - 1  # 0-59
    riganzhi = gz_info["日干支"]
    xunkong = gz_info["旬空"]

    # 时干支
    shichen_idx = get_shichen_index(h)
    shichen = SHI_ZHI[shichen_idx]

    # 时干支：日上起时法
    # 甲己还加甲, 乙庚丙作初, 丙辛从戊起, 丁壬庚子居, 戊癸何方发, 壬子是真途
    RIQI_SHI = {
        "甲": 0, "己": 0,
        "乙": 2, "庚": 2,
        "丙": 4, "辛": 4,
        "丁": 6, "壬": 6,
        "戊": 8, "癸": 8,
    }
    shigan_idx = (RIQI_SHI.get(rigan, 0) + shichen_idx) % 10
    shigan = TIANGAN[shigan_idx]
    shiganzhi = f"{shigan}{shichen}"

    # 节气 → 局数 → 阴阳遁
    jieqi_name, yinyang, (shang_ju, zhong_ju, xia_ju) = get_jieqi(d)
    sanyuan_idx = get_sanyuan(gz_idx)
    sanyuan_name = ["上元", "中元", "下元"][sanyuan_idx]
    jushu = [shang_ju, zhong_ju, xia_ju][sanyuan_idx]
    ju_name = f"{yinyang}{jushu}局({jieqi_name}·{sanyuan_name})"

    # 地盘
    dipan = build_dipan(jushu, yinyang)

    # ── 值符 & 值使 ──
    # 旬首: 时干支所在的旬
    shi_idx = (shigan_idx * 12 + shichen_idx)  # wrong, need proper index
    # 用日干支推算时干支的方法: 子时天干由日干决定
    # 时干支的60干支表索引:
    shi_xun = ((RIQI_SHI.get(rigan, 0) + shichen_idx) % 10 * 12 + shichen_idx) % 60
    # Actually, 时干支在60表中的索引:
    # 甲子=0, 时干shigan, 时支shichen
    # 时支索引shichen_idx, 时干索引shigan_idx
    # 找到甲子时在第一日的偏移
    # 甲子时→0, 甲时天干为甲,子时地支为子
    # 不是这样算的。我就用时干时支直接查。
    shi_gz_idx = None
    for i, gz in enumerate(GANZHI_60):
        if gz == shiganzhi:
            shi_gz_idx = i
            break

    # 旬首
    shi_xun = shi_gz_idx // 10  # 0-5
    xunshou_name = LIUYI_XUNSHOU[LIUYI[shi_xun]]  # e.g. "甲午"
    xunshou_liuyi = LIUYI[shi_xun]  # e.g. "辛" (甲午辛)

    # 旬首六仪在地盘的宫位
    xunshou_gong = find_gong_with_gan(dipan, xunshou_liuyi)

    # 值符星 = 旬首宫对应的原始九星
    zhifu_xing = JIUXING[xunshou_gong - 1] if xunshou_gong != 5 else "天禽"

    # 值使门 = 旬首宫对应的原始八门 (中5寄坤2)
    zhishi_men_gong = xunshou_gong if xunshou_gong != 5 else 2
    zhishi_men = BAMEN[zhishi_men_gong - 1]

    # ── 天盘 ──
    # 值符星加于时干宫。时干在地盘的宫位。
    shigan_gong = find_gong_with_gan(dipan, shigan)

    # 各星按顺序排布
    xing_order = []
    start_idx = JIUXING.index(zhifu_xing)
    if yinyang == "阳遁":
        xing_order = JIUXING[start_idx:] + JIUXING[:start_idx]
    else:
        xing_order = [JIUXING[start_idx]] + JIUXING[start_idx - 1::-1] + JIUXING[:start_idx:-1]
        # 逆排更准确的方法: 值符在第一位,后面递减
        order_list = []
        for i in range(9):
            idx = (start_idx - i) % 9
            order_list.append(JIUXING[idx])
        xing_order = order_list

    tianpan_xing = {}
    if yinyang == "阳遁":
        for i in range(9):
            gong = ((shigan_gong - 1) + i) % 9 + 1
            tianpan_xing[gong] = xing_order[i]
    else:
        for i in range(9):
            gong = ((shigan_gong - 1) - i) % 9 + 1
            tianpan_xing[gong] = xing_order[i]

    # ── 天盘天干 ──
    # 地盘天干随值符星飞转
    # 值符星原宫(旬首宫)的地盘天干 = xunshou_liuyi
    # 这个天干飞到 shigan_gong
    tianpan_gan = {}
    yingong_index = 0 if yinyang == "阳遁" else 2  # 阳顺阴逆, 阴遁逆排用2是因为阴遁地排逆
    # 简化: 用飞转法
    for gong in range(1, 10):
        if yinyang == "阳遁":
            offset = (gong - shigan_gong) % 9
        else:
            offset = -(gong - shigan_gong) % 9
        src_gong = (xunshou_gong - 1 + offset) % 9 + 1
        tianpan_gan[gong] = dipan.get(src_gong, QILI_YUAN[(src_gong - 1) % 9])

    # ── 八门 ──
    # 值使门加于时支宫
    shizhi_gong = shichen_idx + 1  # 子=1,丑=2,...亥=12→亥在哪个宫?
    # 地支→宫位: 子=1坎,丑=8艮,寅=8艮,卯=3震,辰=4巽,巳=4巽,午=9离,未=2坤,申=2坤,酉=7兑,戌=6乾,亥=6乾
    DIZHI_TO_GONG = {
        "子": 1, "丑": 8, "寅": 8, "卯": 3, "辰": 4, "巳": 4,
        "午": 9, "未": 2, "申": 2, "酉": 7, "戌": 6, "亥": 6,
    }
    zhishi_target_gong = DIZHI_TO_GONG[shichen]

    men_list = []
    zhishi_idx = BAMEN.index(zhishi_men)
    # 八门顺序（跳过中5宫）
    bamen_all = [m for m in BAMEN if m]
    if yinyang == "阳遁":
        for i in range(8):
            men_list.append(bamen_all[(zhishi_idx + i) % 8])
    else:
        for i in range(8):
            men_list.append(bamen_all[(zhishi_idx - i) % 8])

    bamen_pan = {}
    gong_order = [1,8,3,4,9,2,7,6]  # 宫位排布顺序(阳顺)
    if yinyang == "阴遁":
        gong_order = [1,6,7,2,9,4,3,8]  # 阴逆

    # Actually, let me use a simpler approach
    # 值使在zhishi_target_gong, 阳顺阴逆排八门
    yg_order = [1,8,3,4,9,2,7,6]  # 阳遁宫序
    yin_gong_order = [1,6,7,2,9,4,3,8]  # 阴遁宫序
    ordered_gongs = yg_order if yinyang == "阳遁" else yin_gong_order

    if zhishi_target_gong not in ordered_gongs:
        zhishi_target_gong = ordered_gongs[0]

    start_pos = ordered_gongs.index(zhishi_target_gong)
    for i, men in enumerate(men_list):
        gong = ordered_gongs[(start_pos + i) % 8]
        bamen_pan[gong] = men

    # ── 八神 ──
    # 值符神随天盘值符星
    zhifu_shen_gong = shigan_gong
    bashen = BASHEN_YANG if yinyang == "阳遁" else BASHEN_YIN
    bashen_pan = {}
    bashen_gong_order = [1,8,3,4,9,2,7,6]  # standard order
    if yinyang == "阴遁":
        bashen_gong_order = [1,6,7,2,9,4,3,8]

    if zhifu_shen_gong not in bashen_gong_order:
        zhifu_shen_gong = 1

    start_shen = bashen_gong_order.index(zhifu_shen_gong)
    for i in range(8):
        shen = bashen[i % 8]
        gong = bashen_gong_order[(start_shen + i) % 8]
        bashen_pan[gong] = shen

    # ── 组装九宫结果 ──
    jiugong = {}
    for gong_num in range(1, 10):
        jiugong[gong_num] = {
            "宫数": gong_num,
            "地盘": dipan.get(gong_num, ""),
            "天盘": tianpan_gan.get(gong_num, ""),
            "九星": tianpan_xing.get(gong_num, ""),
            "八门": bamen_pan.get(gong_num, ""),
            "八神": bashen_pan.get(gong_num, ""),
        }
    # 中5寄坤2
    jiugong[5]["八门"] = jiugong[2]["八门"]

    return {
        "时间": dt.strftime("%Y-%m-%d %H:%M"),
        "日干支": riganzhi,
        "日干": rigan,
        "日支": rizhi,
        "旬空": xunkong,
        "时干支": shiganzhi,
        "时干": shigan,
        "时支": shichen,
        "局": ju_name,
        "节气": jieqi_name,
        "阴阳遁": yinyang,
        "三元": sanyuan_name,
        "局数": jushu,
        "旬首": xunshou_name,
        "值符星": zhifu_xing,
        "值使门": zhishi_men,
        "九宫": jiugong,
    }

# ──────────────────────────────────────────────
# 格式化输出
# ──────────────────────────────────────────────

GONG_NAME = {1:"坎", 2:"坤", 3:"震", 4:"巽", 5:"中", 6:"乾", 7:"兑", 8:"艮", 9:"离"}

def format_output(result: dict) -> str:
    lines = []
    lines.append("╔══════════════════════════════╗")
    lines.append("║        奇门遁甲排盘          ║")
    lines.append("╚══════════════════════════════╝")
    lines.append("")
    lines.append(f"时间: {result['时间']}")
    lines.append(f"日干支: {result['日干支']}  时干支: {result['时干支']}")
    lines.append(f"局: {result['局']}")
    lines.append(f"旬首: {result['旬首']}  值符: {result['值符星']}  值使: {result['值使门']}")
    lines.append(f"旬空: {'、'.join(result['旬空'])}")
    lines.append("")
    lines.append("━━━ 九宫格局 ━━━")
    # 按洛书排列: 4 9 2 / 3 5 7 / 8 1 6
    layout = [[4,9,2],[3,5,7],[8,1,6]]
    for row in layout:
        cells = []
        for gong_num in row:
            jg = result["九宫"]
            g = jg.get(gong_num, jg.get(str(gong_num), {}))
            cell = f"[{GONG_NAME[gong_num]}]"
            cell += f"地:{g.get('地盘',''):2s}"
            cell += f" 天:{g.get('天盘',''):2s}"
            cell += f" 星:{g.get('九星',''):4s}"
            cell += f" 门:{g.get('八门',''):2s}"
            cell += f" 神:{g.get('八神',''):2s}"
            cells.append(cell)
        lines.append("  " + " | ".join(cells))
    lines.append("")
    return "\n".join(lines)

# ──────────────────────────────────────────────
# 主程序
# ──────────────────────────────────────────────

def main():
    if "--json" in sys.argv:
        json_idx = sys.argv.index("--json")
        args = sys.argv[json_idx + 1:]
        if len(args) >= 2:
            dt = datetime.strptime(f"{args[0]} {args[1]}", "%Y-%m-%d %H:%M")
        elif len(args) == 1:
            dt = datetime.strptime(f"{args[0]} 12:00", "%Y-%m-%d %H:%M")
        else:
            dt = datetime.now()
        print(json.dumps(build_qimen(dt), ensure_ascii=False, indent=2))
    elif len(sys.argv) >= 3:
        dt = datetime.strptime(f"{sys.argv[1]} {sys.argv[2]}", "%Y-%m-%d %H:%M")
        print(format_output(build_qimen(dt)))
    elif len(sys.argv) == 2:
        dt = datetime.strptime(f"{sys.argv[1]} 12:00", "%Y-%m-%d %H:%M")
        print(format_output(build_qimen(dt)))
    else:
        print(format_output(build_qimen(datetime.now())))

if __name__ == "__main__":
    main()
