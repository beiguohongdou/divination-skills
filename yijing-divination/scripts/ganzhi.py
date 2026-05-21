#!/usr/bin/env python3
"""
干支换算工具 —— 公历日期转干支日、月建、旬空。

用法：
    python ganzhi.py                    # 使用今天的日期
    python ganzhi.py 2026-05-17         # 指定日期
    python ganzhi.py --json 2026-05-17  # JSON 输出（供 skill 调用）

参考：
    日干支以 1900-01-01 = 甲戌日（第 11 位）为基准推算。
    月建按节气近似日期划分。
    旬空按甲子旬规则计算。
"""

import sys
from datetime import date, timedelta

# ============================================================
# 常量
# ============================================================

TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
SHENGXIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
WUXING_TG = ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水"]   # 天干五行
WUXING_DZ = ["水", "土", "木", "木", "土", "火", "火", "土", "金", "金", "土", "水"]  # 地支五行

# 60 干支表（0=甲子, 1=乙丑, ..., 59=癸亥）
GANZHI_60 = [f"{TIANGAN[i % 10]}{DIZHI[i % 12]}" for i in range(60)]

# 基准日：1900-01-01 = 甲戌日。甲戌在 60 干支表中排第 10 位（0-indexed）
REF_DATE = date(1900, 1, 1)
REF_GZ_INDEX = 10  # 甲戌

# 6 旬的旬空表
# 甲子旬(0-9) → 戌亥空(9,10)  甲戌旬(10-19) → 申酉空(7,8)
# 甲申旬(20-29) → 午未空(5,6)  甲午旬(30-39) → 辰巳空(3,4)
# 甲辰旬(40-49) → 寅卯空(1,2)  甲寅旬(50-59) → 子丑空(0,11)
XUNKONG_MAP = {
    0: (DIZHI[10], DIZHI[11]),   # 甲子旬 → 戌亥
    1: (DIZHI[8], DIZHI[9]),     # 甲戌旬 → 申酉
    2: (DIZHI[6], DIZHI[7]),     # 甲申旬 → 午未
    3: (DIZHI[4], DIZHI[5]),     # 甲午旬 → 辰巳
    4: (DIZHI[2], DIZHI[3]),     # 甲辰旬 → 寅卯
    5: (DIZHI[0], DIZHI[1]),     # 甲寅旬 → 子丑
}

# 月建（节气近似日）
# 寅月: 立春(2/4) → 卯月: 惊蛰(3/6) → 辰月: 清明(4/5) → 巳月: 立夏(5/6)
# 午月: 芒种(6/6) → 未月: 小暑(7/7) → 申月: 立秋(8/7) → 酉月: 白露(9/8)
# 戌月: 寒露(10/8) → 亥月: 立冬(11/7) → 子月: 大雪(12/7) → 丑月: 小寒(1/6)
MONTH_BRANCH = [
    (1, 6,  "丑"),   # 小寒 ~1/6 (approx)
    (2, 4,  "寅"),   # 立春 ~2/4
    (3, 6,  "卯"),   # 惊蛰 ~3/6
    (4, 5,  "辰"),   # 清明 ~4/5
    (5, 6,  "巳"),   # 立夏 ~5/6
    (6, 6,  "午"),   # 芒种 ~6/6
    (7, 7,  "未"),   # 小暑 ~7/7
    (8, 7,  "申"),   # 立秋 ~8/7
    (9, 8,  "酉"),   # 白露 ~9/8
    (10, 8, "戌"),   # 寒露 ~10/8
    (11, 7, "亥"),   # 立冬 ~11/7
    (12, 7, "子"),   # 大雪 ~12/7
]

# ============================================================
# 计算函数
# ============================================================

def days_between(d1: date, d2: date) -> int:
    """两个日期之间的天数差"""
    return (d2 - d1).days

def get_ganzhi_index(d: date) -> int:
    """返回日期 d 在 60 干支表中的索引（0-59）"""
    delta = days_between(REF_DATE, d)
    return (REF_GZ_INDEX + delta) % 60

def get_day_ganzhi(d: date) -> str:
    """返回日期 d 的干支（如 '甲子'）"""
    return GANZHI_60[get_ganzhi_index(d)]

def get_xunkong(d: date) -> tuple:
    """返回日期 d 所在旬的旬空（两个地支元组）"""
    idx = get_ganzhi_index(d)
    xun = idx // 10  # 0-5
    return XUNKONG_MAP[xun]

def get_yuejian(d: date) -> str:
    """返回日期 d 的月建地支"""
    # 按节气近似日查表
    md_key = (d.month, d.day)
    for month_start, day_start, branch in reversed(MONTH_BRANCH):
        if (d.month > month_start) or (d.month == month_start and d.day >= day_start):
            return branch
    return MONTH_BRANCH[-1][2]  # 默认丑月

def get_tiangan_index(dz: str) -> int:
    """地支在十二支中的索引"""
    return DIZHI.index(dz)

def is_chong(dz1: str, dz2: str) -> bool:
    """两地支是否相冲（差6位）"""
    i1, i2 = DIZHI.index(dz1), DIZHI.index(dz2)
    return abs(i1 - i2) == 6

def is_he(dz1: str, dz2: str) -> bool:
    """两地支是否六合"""
    he_pairs = {("子","丑"),("丑","子"),("寅","亥"),("亥","寅"),
                 ("卯","戌"),("戌","卯"),("辰","酉"),("酉","辰"),
                 ("巳","申"),("申","巳"),("午","未"),("未","午")}
    return (dz1, dz2) in he_pairs

def get_dizhi_wuxing(dz: str) -> str:
    """地支对应的五行"""
    return WUXING_DZ[DIZHI.index(dz)]

def get_tiangan_wuxing(tg: str) -> str:
    """天干对应的五行"""
    return WUXING_TG[TIANGAN.index(tg)]

# ============================================================
# 主程序
# ============================================================

def compute(d: date) -> dict:
    """计算日期的所有干支数据"""
    gz = get_day_ganzhi(d)
    tg, dz = gz[0], gz[1]
    xk = get_xunkong(d)
    yj = get_yuejian(d)
    gz_idx = get_ganzhi_index(d)

    return {
        "date": d.isoformat(),
        "日干支": gz,
        "日天干": tg,
        "日地支": dz,
        "天干五行": get_tiangan_wuxing(tg),
        "地支五行": get_dizhi_wuxing(dz),
        "旬空": list(xk),
        "月建": yj,
        "干支序数": gz_idx + 1,  # 1-60
    }

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        # JSON 输出模式
        import json
        d = date.today()
        if len(sys.argv) > 2:
            d = date.fromisoformat(sys.argv[2])
        print(json.dumps(compute(d), ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1:
        d = date.fromisoformat(sys.argv[1])
        result = compute(d)
        print(f"日期: {result['date']}")
        print(f"日干支: {result['日干支']} (第{result['干支序数']}位)")
        print(f"天干: {result['日天干']}({result['天干五行']})  地支: {result['日地支']}({result['地支五行']})")
        print(f"旬空: {'、'.join(result['旬空'])}")
        print(f"月建: {result['月建']}月")
    else:
        d = date.today()
        result = compute(d)
        print(f"今日: {result['date']}")
        print(f"日干支: {result['日干支']} (第{result['干支序数']}位)")
        print(f"天干: {result['日天干']}({result['天干五行']})  地支: {result['日地支']}({result['地支五行']})")
        print(f"旬空: {'、'.join(result['旬空'])}")
        print(f"月建: {result['月建']}月")
        print()
        # 额外：显示今日的六神起始
        liu_shen_start = {
            "甲": "青龙", "乙": "青龙",
            "丙": "朱雀", "丁": "朱雀",
            "戊": "勾陈", "己": "螣蛇",
            "庚": "白虎", "辛": "白虎",
            "壬": "玄武", "癸": "玄武",
        }
        print(f"六神起始: {liu_shen_start.get(result['日天干'], '?')}")

if __name__ == "__main__":
    main()
