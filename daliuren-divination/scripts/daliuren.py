#!/usr/bin/env python3
"""
大六壬排盘工具 —— 输入公历日期和时间，输出天地盘、四课、三传、十二天将。

用法：
    python daliuren.py                              # 使用当前日期和时间
    python daliuren.py 2026-05-22 14:30             # 指定日期和时间
    python daliuren.py --json 2026-05-22 14:30      # JSON 输出

依赖：
    本脚本需与 ganzhi.py 放在同一目录，或已安装至 Python path。
"""

import sys
import os
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

# 月将名
YUEJIANG_NAME = [
    "神后", "大吉", "功曹", "太冲", "天罡", "太乙",
    "胜光", "小吉", "传送", "从魁", "河魁", "登明",
]

# 月将地支（中气后切换）: (节,日,月将地支,月将序号)
# 用地支：子=0,丑=1,...,亥=11
YUEJIANG_SWITCH = [
    ( 1, 21,  0, "神后"),    # 大寒后 → 子(神后)
    ( 2, 19,  11, "登明"),   # 雨水后 → 亥(登明)
    ( 3, 21,  10, "河魁"),   # 春分后 → 戌(河魁)
    ( 4, 21,   9, "从魁"),   # 谷雨后 → 酉(从魁)
    ( 5, 22,   8, "传送"),   # 小满后 → 申(传送)
    ( 6, 22,   7, "小吉"),   # 夏至后 → 未(小吉)
    ( 7, 23,   6, "胜光"),   # 大暑后 → 午(胜光)
    ( 8, 24,   5, "太乙"),   # 处暑后 → 巳(太乙)
    ( 9, 24,   4, "天罡"),   # 秋分后 → 辰(天罡)
    (10, 24,   3, "太冲"),   # 霜降后 → 卯(太冲)
    (11, 23,   2, "功曹"),   # 小雪后 → 寅(功曹)
    (12, 22,   1, "大吉"),   # 冬至后 → 丑(大吉)
]

# 日干寄宫
GANGONG = {
    "甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳",
    "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑",
}

# 天将：十二贵神顺序
TIANJIANG_ORDER = [
    "贵人", "螣蛇", "朱雀", "六合", "勾陈", "青龙",
    "天空", "白虎", "太常", "玄武", "太阴", "天后",
]

# 贵人口诀（昼贵 / 夜贵，用地支名）
# 甲戊庚牛羊(丑未), 乙己鼠猴乡(子申), 丙丁猪鸡位(亥酉),
# 壬癸兔蛇藏(卯巳), 六辛逢马虎(午寅), 此是贵人方。
GUI_REN_TABLE = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "壬": ("卯", "巳"), "癸": ("卯", "巳"),
    "辛": ("午", "寅"),
}

# 时辰地支表
SHI_ZHI = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# 天干五行
TG_WX = {tg: wx for tg, wx in zip(TIANGAN, WUXING_TG)}
# 地支五行
DZ_WX = {dz: wx for dz, wx in zip(DIZHI, WUXING_DZ)}

# 五行生克 (key 克 value)
WUXING_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 天干阴阳
YANG_GAN = set("甲丙戊庚壬")
YIN_GAN = set("乙丁己辛癸")

# ──────────────────────────────────────────────
# 核心计算函数
# ──────────────────────────────────────────────

def get_yuejiang(d: date) -> dict:
    """根据日期返回月将（中气法）"""
    for m, day, idx, name in reversed(YUEJIANG_SWITCH):
        if d.month > m or (d.month == m and d.day >= day):
            return {"地支": DIZHI[idx], "序号": idx, "名称": name}
    return {"地支": DIZHI[1], "序号": 1, "名称": "大吉"}  # 默认

def get_shichen_index(hour: int) -> int:
    """将小时转换为时辰地支索引（0=子,1=丑,...,11=亥）"""
    return ((hour + 1) // 2) % 12 if hour != 23 else 0

def build_tiandipan(yuejiang_idx: int, shichen_idx: int):
    """
    天地盘。
    月将加于占时。地盘固定：子丑寅卯...(0-11)。
    天盘[b] = (月将 + (b - 占时) + 12) % 12
    """
    tiandi = {}
    for b in range(12):
        t = (yuejiang_idx + (b - shichen_idx)) % 12
        tiandi[DIZHI[b]] = DIZHI[t]
    return tiandi

def get_shangshen(gong: str, tiandipan: dict) -> str:
    """获取某宫的上神（天盘加临之神）"""
    return tiandipan[gong]

def build_sike(rigan: str, rizhi: str, tiandipan: dict):
    """
    起四课。
    一课：日干寄宫上神
    二课：一课之上神
    三课：日支上神
    四课：三课之上神
    """
    gangong = GANGONG[rigan]
    ke1 = get_shangshen(gangong, tiandipan)
    ke2 = get_shangshen(ke1, tiandipan)
    ke3 = get_shangshen(rizhi, tiandipan)
    ke4 = get_shangshen(ke3, tiandipan)
    return {
        "一课": {"下": gangong, "上": ke1},
        "二课": {"下": ke1, "上": ke2},
        "三课": {"下": rizhi, "上": ke3},
        "四课": {"下": ke3, "上": ke4},
    }

def ke_check(ke_dict, tiandipan):
    """
    检查一课是否有克。
    xia_wx克shang_wx → 下克上(贼)
    shang_wx克xia_wx → 上克下(克)
    返回: None(无克), ('下克上',下地支), ('上克下',上地支)
    """
    xia = ke_dict["下"]
    shang = ke_dict["上"]
    xia_wx = DZ_WX[xia]
    shang_wx = DZ_WX[shang]
    if WUXING_KE.get(xia_wx) == shang_wx:
        return ("下克上", xia)  # 贼
    if WUXING_KE.get(shang_wx) == xia_wx:
        return ("上克下", shang)  # 克
    return None

def get_sanchuan_jiuzongmen(sike, rigan, rizhi, tiandipan):
    """
    九宗门起三传。
    返回: {"初传": ..., "中传": ..., "末传": ..., "宗门": "..."}
    """
    ke_names = ["一课", "二课", "三课", "四课"]
    ke_data = []
    for name in ke_names:
        result = ke_check(sike[name], tiandipan)
        ke_data.append({
            "name": name,
            "result": result,
            "shangshen": sike[name]["上"],
        })

    # 收集所有克
    zei = []  # 下克上
    ke = []   # 上克下
    for kd in ke_data:
        if kd["result"] is None:
            continue
        ktype, dz = kd["result"]
        if ktype == "下克上":
            zei.append(dz)
        else:
            ke.append(dz)

    chuchuan = None
    zongmen = ""

    # ── 1. 有克 ──
    all_ke = zei + ke
    if all_ke:
        # 先用贼
        if len(zei) == 1:
            chuchuan = zei[0]
            zongmen = "贼克法(下克上)"
        elif len(zei) > 1:
            # 多个贼 → 比用
            chuchuan = _biyong(zei, rigan)
            zongmen = f"比用(多贼,取与日干同阴阳)"
        elif len(ke) == 1:
            chuchuan = ke[0]
            zongmen = "贼克法(上克下)"
        else:
            # 多个克 → 比用
            chuchuan = _biyong(ke, rigan)
            zongmen = f"比用(多克,取与日干同阴阳)"

        if chuchuan is None:
            # 比用也选不出 → 涉害
            candidates = zei if zei else ke
            chuchuan = _shehai(candidates, sike, tiandipan)
            zongmen = "涉害法"
    else:
        # ── 2. 无克 → 遥克 ──
        chuchuan = _yaoke(rigan, rizhi, ke_data)
        if chuchuan:
            zongmen = "遥克法"
        else:
            # ── 3. 无遥克 → 昴星 ──
            return _maoxing(rigan, sike, tiandipan)

    # 从初传到中传、末传
    chuchuan_idx = DIZHI.index(chuchuan)
    zhongchuan = tiandipan[chuchuan]  # 中传 = 初传地盘所临天盘之神
    mochuan = tiandipan[zhongchuan]   # 末传 = 中传地盘所临天盘之神

    return {
        "初传": chuchuan,
        "中传": zhongchuan,
        "末传": mochuan,
        "宗门": zongmen,
    }

def _biyong(candidates, rigan):
    """比用法：取与日干同阴阳者。阳干取阳支，阴干取阴支。"""
    is_yang = rigan in YANG_GAN
    yang_dz = set("子寅辰午申戌")
    yin_dz = set("丑卯巳未酉亥")
    matched = [dz for dz in candidates if (dz in yang_dz) == is_yang]
    if len(matched) == 1:
        return matched[0]
    return None

def _shehai(candidates, sike, tiandipan):
    """涉害法：取受克深者（简化版：取先出现者）"""
    # 完整涉害需要逐位比较克数，此处简化取第一个
    return candidates[0]

def _yaoke(rigan, rizhi, ke_data):
    """遥克法：日干遥克上神，或上神遥克日干"""
    rigan_wx = TG_WX[rigan]
    rizhi_wx = DZ_WX[rizhi]

    # 日干遥克上神
    for kd in ke_data:
        shangshen = kd["shangshen"]
        shangshen_wx = DZ_WX[shangshen]
        if WUXING_KE.get(rigan_wx) == shangshen_wx:
            return shangshen

    # 上神遥克日干
    for kd in ke_data:
        shangshen = kd["shangshen"]
        shangshen_wx = DZ_WX[shangshen]
        if WUXING_KE.get(shangshen_wx) == rigan_wx:
            return shangshen

    return None

def _maoxing(rigan, sike, tiandipan):
    """昴星法：阳日取酉上神为初传，阴日取酉下神为初传"""
    is_yang = rigan in YANG_GAN
    # 酉上神
    you_shang = tiandipan["酉"]
    if is_yang:
        chuchuan = you_shang
    else:
        # 阴日：酉下神 = 谁的天盘是酉
        you_xia = None
        for dz in DIZHI:
            if tiandipan[dz] == "酉":
                you_xia = dz
                break
        chuchuan = you_xia if you_xia else you_shang

    zhongchuan = tiandipan[chuchuan]
    mochuan = tiandipan[zhongchuan]

    return {
        "初传": chuchuan,
        "中传": zhongchuan,
        "末传": mochuan,
        "宗门": "昴星法",
    }

# ──────────────────────────────────────────────
# 十二天将
# ──────────────────────────────────────────────

def get_gui_ren_distribution(rigan: str, shichen_idx: int):
    """
    十二天将分布。
    先找贵人（昼/夜），再顺或逆排十二将。
    贵人临地盘某宫后，阳贵顺排、阴贵逆排。
    规则：甲戊庚日昼贵在丑、夜贵在未。贵人在亥至辰(0-3,10-11)则顺，在巳至戌(4-9)则逆。
    """
    # 判断昼/夜：卯至申(5-15时)为昼，酉至寅(17-3时)为夜
    hour = (shichen_idx * 2) % 24  # 近似
    is_day = 5 <= hour < 17

    day_gui, night_gui = GUI_REN_TABLE.get(rigan, ("子","子"))
    guiren_dz = day_gui if is_day else night_gui
    guiren_idx = DIZHI.index(guiren_dz)

    # 判断顺逆：贵人在亥子丑寅卯辰(10,11,0,1,2,3)则顺，在巳午未申酉戌(4-9)则逆
    shun = guiren_idx in (0, 1, 2, 3, 10, 11)

    tianjiang_pan = {}
    for i, jiang in enumerate(TIANJIANG_ORDER):
        if shun:
            offset = i
        else:
            offset = -i
        pos = (guiren_idx + offset) % 12
        tianjiang_pan[DIZHI[pos]] = jiang

    return {
        "昼夜": "昼" if is_day else "夜",
        "贵神": guiren_dz,
        "顺逆": "顺" if shun else "逆",
        "天将分布": tianjiang_pan,
    }

# ──────────────────────────────────────────────
# 综合排盘
# ──────────────────────────────────────────────

def compute(dt: datetime) -> dict:
    """排一局完整的大六壬盘"""
    d = dt.date()
    h = dt.hour

    # 干支基础数据
    gz_info = ganzhi_compute(d)
    rigan = gz_info["日天干"]
    rizhi = gz_info["日地支"]
    yuejian = gz_info["月建"]
    xunkong = gz_info["旬空"]

    # 月将 & 占时
    yuejiang = get_yuejiang(d)
    shichen_idx = get_shichen_index(h)
    shichen = SHI_ZHI[shichen_idx]

    # 天地盘
    tiandipan = build_tiandipan(yuejiang["序号"], shichen_idx)

    # 四课
    sike = build_sike(rigan, rizhi, tiandipan)

    # 三传（九宗门）
    sanchuan = get_sanchuan_jiuzongmen(sike, rigan, rizhi, tiandipan)

    # 十二天将
    guiren = get_gui_ren_distribution(rigan, shichen_idx)

    # 组装天地盘展示
    tiandi_display = {}
    for dz in DIZHI:
        tiandi_display[dz] = {
            "地盘": dz,
            "天盘": tiandipan[dz],
            "天将": guiren["天将分布"].get(dz, ""),
        }

    return {
        "时间": dt.strftime("%Y-%m-%d %H:%M"),
        "日干支": gz_info["日干支"],
        "日干": rigan,
        "日支": rizhi,
        "旬空": xunkong,
        "月建": yuejian,
        "月将": f'{yuejiang["名称"]}({yuejiang["地支"]})',
        "占时": shichen,
        "天地盘": tiandi_display,
        "四课": sike,
        "三传": sanchuan,
        "贵人": {
            "昼夜": guiren["昼夜"],
            "贵神": guiren["贵神"],
            "顺逆": guiren["顺逆"],
            "天将分布": guiren["天将分布"],
        },
    }

# ──────────────────────────────────────────────
# 格式化输出
# ──────────────────────────────────────────────

def format_output(result: dict) -> str:
    lines = []
    lines.append("╔══════════════════════════════╗")
    lines.append("║        大六壬排盘            ║")
    lines.append("╚══════════════════════════════╝")
    lines.append("")
    lines.append(f"时间: {result['时间']}")
    lines.append(f"日干支: {result['日干支']}  日干: {result['日干']}  日支: {result['日支']}")
    lines.append(f"旬空: {'、'.join(result['旬空'])}")
    lines.append(f"月建: {result['月建']}月  月将: {result['月将']}  占时: {result['占时']}")
    lines.append("")
    lines.append("━━━ 天地盘 ━━━")
    lines.append("  地盘  天盘  天将")
    for dz in DIZHI:
        td = result["天地盘"][dz]
        mark = " ←占时" if dz == result["占时"] else ""
        lines.append(f"  {td['地盘']:4s}  {td['天盘']:4s}  {td['天将']:4s}{mark}")
    lines.append("")
    lines.append("━━━ 四课 ━━━")
    sike = result["四课"]
    lines.append(f"  一课: {sike['一课']['上']}({sike['一课']['下']})  二课: {sike['二课']['上']}({sike['二课']['下']})")
    lines.append(f"  三课: {sike['三课']['上']}({sike['三课']['下']})  四课: {sike['四课']['上']}({sike['四课']['下']})")
    lines.append("")
    lines.append("━━━ 三传 ━━━")
    sc = result["三传"]
    lines.append(f"  宗门: {sc['宗门']}")
    lines.append(f"  初传: {sc['初传']} → 中传: {sc['中传']} → 末传: {sc['末传']}")
    lines.append("")
    lines.append("━━━ 贵人 ━━━")
    gr = result["贵人"]
    lines.append(f"  昼/夜: {gr['昼夜']}  贵神: {gr['贵神']}  顺/逆: {gr['顺逆']}")
    return "\n".join(lines)

# ──────────────────────────────────────────────
# 主程序
# ──────────────────────────────────────────────

def main():
    if "--json" in sys.argv:
        import json
        json_idx = sys.argv.index("--json")
        args = sys.argv[json_idx + 1:]
        if len(args) >= 2:
            dt = datetime.strptime(f"{args[0]} {args[1]}", "%Y-%m-%d %H:%M")
        elif len(args) == 1:
            dt = datetime.strptime(f"{args[0]} 12:00", "%Y-%m-%d %H:%M")
        else:
            dt = datetime.now()
        print(json.dumps(compute(dt), ensure_ascii=False, indent=2))
    elif len(sys.argv) >= 3:
        dt = datetime.strptime(f"{sys.argv[1]} {sys.argv[2]}", "%Y-%m-%d %H:%M")
        print(format_output(compute(dt)))
    elif len(sys.argv) == 2:
        dt = datetime.strptime(f"{sys.argv[1]} 12:00", "%Y-%m-%d %H:%M")
        print(format_output(compute(dt)))
    else:
        print(format_output(compute(datetime.now())))

if __name__ == "__main__":
    main()
