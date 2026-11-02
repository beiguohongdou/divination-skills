#!/usr/bin/env python3
"""钟表时间先校正，再交给排盘。

默认不改时刻：不传经度、不确认夏令时、日界 same-day 时，返回的入盘时间与输入相同。

真太阳时 = 标准时 +（经度 − 120）× 4 分钟 + 均时差（NOAA 近似式）。
夏令时只判定 1986–1991，不自动扣；`--confirm-dst` 才减 60 分钟。
晚子时默认算当天；`--day-boundary next-day` 只把 23:00–23:59 的日期加一天。

夏令时区间（凌晨 2:00 起算，结束日 2:00 止）：
  1986-05-04 .. 1986-09-14   国务院办公厅 1986-04-12 公告
  1987-04-12 .. 1987-09-13   国务院办公厅 1987-02-15 公告
  1988-04-17 .. 1988-09-11   国办 1987-09-09：4 月中旬 / 9 月中旬第一个星期日
  1989-04-16 .. 1989-09-17
  1990-04-15 .. 1990-09-16
  1991-04-14 .. 1991-09-15
"""

from __future__ import annotations

import math
import sys
from datetime import datetime, timedelta

# (start inclusive, end exclusive), both at 02:00 wall clock
DST_SPANS = {
    1986: (datetime(1986, 5, 4, 2, 0), datetime(1986, 9, 14, 2, 0)),
    1987: (datetime(1987, 4, 12, 2, 0), datetime(1987, 9, 13, 2, 0)),
    1988: (datetime(1988, 4, 17, 2, 0), datetime(1988, 9, 11, 2, 0)),
    1989: (datetime(1989, 4, 16, 2, 0), datetime(1989, 9, 17, 2, 0)),
    1990: (datetime(1990, 4, 15, 2, 0), datetime(1990, 9, 16, 2, 0)),
    1991: (datetime(1991, 4, 14, 2, 0), datetime(1991, 9, 15, 2, 0)),
}

DAY_BOUNDARIES = ("same-day", "next-day")


def _leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def equation_of_time_minutes(year: int, month: int, day: int, hour: int = 12, minute: int = 0) -> float:
    """NOAA 均时差，单位分钟。正值表示真太阳时快于平太阳时。"""
    days = 366 if _leap(year) else 365
    doy = datetime(year, month, day).timetuple().tm_yday
    gamma = (2 * math.pi / days) * (doy - 1 + (hour + minute / 60 - 12) / 24)
    return 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )


def longitude_correction_minutes(lon: float) -> float:
    """相对东经 120°。偏西为负。"""
    return (float(lon) - 120.0) * 4.0


def dst_active(dt: datetime) -> bool:
    span = DST_SPANS.get(dt.year)
    if span is None:
        return False
    start, end = span
    return start <= dt < end


def resolve_clock(dt: datetime, *, lon: float | None = None, confirm_dst: bool = False, day_boundary: str = "same-day") -> tuple[datetime, dict]:
    """返回 (入盘时间, 时间校正)。"""
    if day_boundary not in DAY_BOUNDARIES:
        raise ValueError("day_boundary 只能是 same-day 或 next-day")

    wall = dt
    working = dt
    if dst_active(working) and confirm_dst:
        working = working - timedelta(hours=1)
        dst_label = "已扣60分钟"
    elif dst_active(wall):
        dst_label = "在区间，未扣"
    else:
        dst_label = "不在区间"

    if lon is None:
        pan = working
        solar_label = "未校正"
    else:
        eot = equation_of_time_minutes(working.year, working.month, working.day, working.hour, working.minute)
        corr = longitude_correction_minutes(lon) + eot
        pan = working + timedelta(seconds=round(corr * 60))
        pan = pan.replace(second=0, microsecond=0)
        solar_label = "已校正"

    if day_boundary == "next-day" and pan.hour == 23:
        pan = pan + timedelta(days=1)

    # 没做任何校正时保留原对象，避免无谓丢掉秒
    if lon is None and dst_label != "已扣60分钟" and pan == working:
        pan = wall

    meta = {
        "输入钟面": wall.strftime("%Y-%m-%d %H:%M"),
        "入盘时间": pan.strftime("%Y-%m-%d %H:%M"),
        "经度": None if lon is None else float(lon),
        "真太阳时": solar_label,
        "夏令时": dst_label,
        "日界": day_boundary,
    }
    return pan, meta


def consume_clock_args(argv: list[str]) -> tuple[list[str], dict]:
    """从 argv 摘出 --lon / --confirm-dst / --day-boundary，其余原样返回。"""
    rest: list[str] = []
    lon = None
    confirm_dst = False
    day_boundary = "same-day"
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--lon":
            if i + 1 >= len(argv):
                raise SystemExit("--lon 需要一个经度数字")
            lon = float(argv[i + 1])
            i += 2
            continue
        if a == "--confirm-dst":
            confirm_dst = True
            i += 1
            continue
        if a == "--day-boundary":
            if i + 1 >= len(argv):
                raise SystemExit("--day-boundary 需要 same-day 或 next-day")
            day_boundary = argv[i + 1]
            if day_boundary not in DAY_BOUNDARIES:
                raise SystemExit("day-boundary 只能是 same-day 或 next-day")
            i += 2
            continue
        rest.append(a)
        i += 1
    return rest, {"lon": lon, "confirm_dst": confirm_dst, "day_boundary": day_boundary}


def self_check() -> None:
    """不改默认盘；经度、夏令时、日界三条路径各有一条断言。"""
    wall = datetime(2026, 7, 4, 6, 0)
    pan, meta = resolve_clock(wall)
    assert pan == wall and meta["真太阳时"] == "未校正" and meta["夏令时"] == "不在区间"
    assert meta["日界"] == "same-day"

    assert longitude_correction_minutes(87) < 0
    assert longitude_correction_minutes(120) == 0
    pan87, meta87 = resolve_clock(wall, lon=87)
    assert meta87["真太阳时"] == "已校正" and meta87["入盘时间"] != meta87["输入钟面"]

    summer = datetime(1988, 7, 1, 12, 0)
    hold, hold_meta = resolve_clock(summer)
    assert hold == summer and hold_meta["夏令时"] == "在区间，未扣"
    cut, cut_meta = resolve_clock(summer, confirm_dst=True)
    assert cut == datetime(1988, 7, 1, 11, 0) and cut_meta["夏令时"] == "已扣60分钟"

    late = datetime(2026, 11, 2, 23, 30)
    same, same_meta = resolve_clock(late)
    assert same == late and same_meta["日界"] == "same-day"
    nxt, nxt_meta = resolve_clock(late, day_boundary="next-day")
    assert nxt == datetime(2026, 11, 3, 23, 30) and nxt_meta["日界"] == "next-day"
    early, _ = resolve_clock(datetime(2026, 11, 3, 0, 30), day_boundary="next-day")
    assert early == datetime(2026, 11, 3, 0, 30)


if __name__ == "__main__":
    try:
        self_check()
    except AssertionError as e:
        print(f"FAIL {e}")
        sys.exit(1)
    print("clock_adjust self_check PASS")
