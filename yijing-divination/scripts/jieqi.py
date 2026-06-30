#!/usr/bin/env python3
"""
二十四节气 —— 基于 ephem 太阳黄经计算交节时刻（Asia/Shanghai 本地时刻）。

用法：
    py -3 jieqi.py --json 2026-07-04
    py -3 jieqi.py --json 2026-07-04 06:00

依赖：pip install ephem
"""

from __future__ import annotations

import math
import sys
from datetime import date, datetime, timedelta, timezone

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import ephem
except ImportError:
    ephem = None  # type: ignore

# 24 节气：名称, 黄经(度), 是否「节」（月建切换点）
JIEQI_24 = [
    ("小寒", 285, False), ("大寒", 300, True),
    ("立春", 315, True), ("雨水", 330, False),
    ("惊蛰", 345, True), ("春分", 0, False),
    ("清明", 15, True), ("谷雨", 30, False),
    ("立夏", 45, True), ("小满", 60, False),
    ("芒种", 75, True), ("夏至", 90, False),
    ("小暑", 105, True), ("大暑", 120, False),
    ("立秋", 135, True), ("处暑", 150, False),
    ("白露", 165, True), ("秋分", 180, False),
    ("寒露", 195, True), ("霜降", 210, False),
    ("立冬", 225, True), ("小雪", 240, False),
    ("大雪", 255, True), ("冬至", 270, False),
]

# 节 → 月建（寅月起于立春）
JIE_JIAN = {
    "立春": "寅", "惊蛰": "卯", "清明": "辰", "立夏": "巳",
    "芒种": "午", "小暑": "未", "立秋": "申", "白露": "酉",
    "寒露": "戌", "立冬": "亥", "大雪": "子", "小寒": "丑",
}

# 中气 → 大六壬月将（中气后切换）
QI_YUEJIANG = {
    "大寒": ("神后", "子"), "雨水": ("登明", "亥"), "春分": ("河魁", "戌"),
    "谷雨": ("从魁", "酉"), "小满": ("传送", "申"), "夏至": ("小吉", "未"),
    "大暑": ("胜光", "午"), "处暑": ("太乙", "巳"), "秋分": ("天罡", "辰"),
    "霜降": ("太冲", "卯"), "小雪": ("功曹", "寅"), "冬至": ("大吉", "丑"),
}

TZ_CN = timezone(timedelta(hours=8))


def _require_ephem() -> None:
    if ephem is None:
        raise RuntimeError("缺少依赖 ephem，请运行: pip install ephem")


def sun_ecliptic_lon_deg(t: datetime) -> float:
    _require_ephem()
    utc = t.astimezone(timezone.utc)
    obs = ephem.Observer()
    obs.date = utc.strftime("%Y/%m/%d %H:%M:%S")
    eq = ephem.Equatorial(ephem.Sun(obs.date), epoch=obs.epoch)
    el = ephem.Ecliptic(eq)
    return math.degrees(el.lon) % 360


def find_term_time(year: int, lon_deg: float) -> datetime:
    """求 year 年内太阳到达黄经 lon_deg 的北京时间（近似搜索 + 二分）。"""
    _require_ephem()
    # 每个节气约间隔 15 天，从该年 1 月 1 日起步进搜索
    if lon_deg >= 285:
        start = datetime(year, 1, 1, tzinfo=TZ_CN)
    elif lon_deg < 90:
        start = datetime(year, 3, 1, tzinfo=TZ_CN)
    else:
        start = datetime(year, 6, 1, tzinfo=TZ_CN)

    t0 = start
    step = timedelta(hours=6)
    prev_lon = sun_ecliptic_lon_deg(t0)
    t = t0 + step
    while t.year <= year + 1:
        cur_lon = sun_ecliptic_lon_deg(t)
        # 检测是否跨过目标黄经
        def crossed(a: float, b: float, target: float) -> bool:
            da = (b - a) % 360
            dtg = (target - a) % 360
            return da >= dtg and da < 180

        if crossed(prev_lon, cur_lon, lon_deg):
            lo, hi = t - step, t
            for _ in range(40):
                mid = lo + (hi - lo) / 2
                if sun_ecliptic_lon_deg(mid) < lon_deg:
                    lo = mid
                else:
                    hi = mid
            return hi
        prev_lon = cur_lon
        t += step
    raise ValueError(f"未找到 {year} 年黄经 {lon_deg}° 交节时刻")


def term_schedule(year: int) -> list[dict]:
    out = []
    for name, lon, is_jie in JIEQI_24:
        dt = find_term_time(year, lon)
        out.append({
            "名称": name,
            "黄经": lon,
            "是否节": is_jie,
            "交节北京时间": dt.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return out


def resolve_at(dt: datetime) -> dict:
    """给定时刻，返回当前节气、月建、月将及精度说明。"""
    _require_ephem()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ_CN)
    else:
        dt = dt.astimezone(TZ_CN)

    y = dt.year
    # 小寒在公历年初可能属上一岁次 schedule，合并两年节气表
    events: list[tuple[datetime, str, bool]] = []
    for yr in (y - 1, y, y + 1):
        for name, lon, is_jie in JIEQI_24:
            try:
                t = find_term_time(yr, lon)
            except ValueError:
                continue
            events.append((t, name, is_jie))
    events.sort(key=lambda x: x[0])

    current = events[0]
    for ev in events:
        if ev[0] <= dt:
            current = ev
        else:
            break

    term_name = current[1]
    # 月建：取最近的「节」
    yuejian = "丑"
    for t, name, is_jie in reversed(events):
        if t <= dt and is_jie and name in JIE_JIAN:
            yuejian = JIE_JIAN[name]
            break

    yuejiang_name, yuejiang_dz = ("神后", "子")
    for t, name, _ in reversed(events):
        if t <= dt and name in QI_YUEJIANG:
            yuejiang_name, yuejiang_dz = QI_YUEJIANG[name]
            break

    return {
        "查询时刻": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "当前节气": term_name,
        "月建": yuejian,
        "月将": {"名": yuejiang_name, "地支": yuejiang_dz},
        "月建精度": "ephem_solar_longitude",
        "月建说明": "按 ephem 太阳黄经计算交节时刻，北京时间；精度优于固定日期表",
    }


def get_yuejian_for_date(d: date, hour: int = 12, minute: int = 0) -> dict:
    dt = datetime(d.year, d.month, d.day, hour, minute, tzinfo=TZ_CN)
    return resolve_at(dt)


def main() -> None:
    import argparse
    import json

    p = argparse.ArgumentParser(description="二十四节气与月建")
    p.add_argument("date_pos", nargs="?", help="YYYY-MM-DD")
    p.add_argument("time_pos", nargs="?", help="HH:MM")
    p.add_argument("--year", type=int, help="输出整年交节表")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    try:
        if args.year:
            result = {"年份": args.year, "节气表": term_schedule(args.year)}
        elif args.date_pos:
            tpart = args.time_pos or "12:00"
            dt = datetime.strptime(f"{args.date_pos} {tpart}", "%Y-%m-%d %H:%M").replace(tzinfo=TZ_CN)
            result = resolve_at(dt)
        else:
            result = resolve_at(datetime.now(TZ_CN))
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if "节气表" in result:
            for row in result["节气表"]:
                print(f"{row['交节北京时间']}  {row['名称']}")
        else:
            print(f"{result['查询时刻']}  节气:{result['当前节气']}  月建:{result['月建']}  月将:{result['月将']['名']}")


if __name__ == "__main__":
    main()
