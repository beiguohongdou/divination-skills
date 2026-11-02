#!/usr/bin/env python3
"""排盘结构铁律，外加这次六项改动的锚点。失败则退出码 1。"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "yijing-divination" / "scripts"))
sys.path.insert(0, str(ROOT / "daliuren-divination" / "scripts"))
sys.path.insert(0, str(ROOT / "qimen-dunjia" / "scripts"))

import clock_adjust  # noqa: E402
import daliuren  # noqa: E402
import meihua_time  # noqa: E402
import qimen  # noqa: E402
from ganzhi import DIZHI, is_chong  # noqa: E402

failures = 0


def fail(msg: str) -> None:
    global failures
    failures += 1
    print(f"FAIL {msg}")


def ok(msg: str) -> None:
    print(f"PASS {msg}")


SHENGKE = {"体生用", "用生体", "体克用", "用克体", "体用比和"}
QILI = set("戊己庚辛壬癸丁丙乙")
MEN = {"休", "死", "伤", "杜", "开", "惊", "生", "景"}


def check_structure() -> None:
    n = 0
    for year in (1988, 2000, 2012, 2026):
        for month in (1, 5, 9):
            for hour in (0, 6, 12, 18):
                dt = datetime(year, month, 15, hour, 0)
                n += 1
                tag = dt.strftime("%Y-%m-%d %H:%M")
                lr = daliuren.compute(dt)
                td = lr["天地盘"]
                if set(td) != set(DIZHI):
                    fail(f"六壬地盘 {tag} 不是十二支各一次")
                tian = [td[z]["天盘"] for z in DIZHI]
                if set(tian) != set(DIZHI):
                    fail(f"六壬天盘 {tag} 不是十二支的排列")
                if set(lr["四课"]) != {"一课", "二课", "三课", "四课"}:
                    fail(f"六壬四课 {tag}")
                sc = lr["三传"]
                if "未实现" not in sc["宗门"]:
                    if any(sc[k] not in DIZHI for k in ("初传", "中传", "末传")):
                        fail(f"六壬三传 {tag} {sc}")
                if "时间校正" not in lr:
                    fail(f"六壬缺时间校正 {tag}")

                qm = qimen.build_qimen(dt)
                jg = qm["九宫"]
                if set(jg) != set(range(1, 10)):
                    fail(f"奇门宫数 {tag}")
                stems = [jg[i]["地盘"] for i in range(1, 10)]
                if set(stems) != QILI:
                    fail(f"奇门地盘天干 {tag} {stems}")
                if qm["时支"] not in DIZHI:
                    fail(f"奇门时支 {tag}")
                for i in range(1, 10):
                    if jg[i]["八门"] not in MEN:
                        fail(f"奇门八门 {tag} 宫{i}={jg[i]['八门']}")
                if set(qm["格局"]) - qimen.GEJU_NAMES:
                    fail(f"奇门格局越界 {tag} {qm['格局']}")

                mh = meihua_time.compute(dt)
                if mh["动爻"] not in range(1, 7):
                    fail(f"梅花动爻 {tag} {mh['动爻']}")
                if not mh["本卦"].get("name") or not mh["变卦"].get("name"):
                    fail(f"梅花卦名 {tag}")
                if mh["体用"]["生克"] not in SHENGKE:
                    fail(f"梅花体用 {tag} {mh['体用']['生克']}")
    ok(f"结构扫描 {n} 个时刻")


def check_anchors() -> None:
    mh = meihua_time.compute(datetime(2026, 7, 4, 6, 0))
    if not (
        mh["本卦"]["name"] == "地雷复"
        and mh["取数"]["年数"]["值"] == 7
        and mh["变卦"]["name"] == "山雷颐"
        and mh["体用"]["生克"] == "体克用"
        and mh["时间校正"]["真太阳时"] == "未校正"
    ):
        fail(f"梅花金盘 {mh['本卦']['name']} 年数={mh['取数']['年数']['值']} {mh['体用']['生克']}")
    else:
        ok("梅花金盘 地雷复 / 7 / 山雷颐 / 体克用")

    lr = daliuren.compute(datetime(2026, 7, 1, 10, 0))
    if lr["三传"]["初传"] != "辰" or "贼克" not in lr["三传"]["宗门"]:
        fail(f"六壬贼克 {lr['三传']}")
    else:
        ok("六壬贼克初传辰")

    gui = daliuren.compute(datetime(2026, 7, 27, 10, 0))
    if gui["贵人"]["贵神"] != "巳":
        fail(f"六壬贵人 {gui['贵人']['贵神']}")
    else:
        ok("六壬贵人巳")

    qm = qimen.build_qimen(datetime(2026, 2, 24, 12, 0))
    if qm["三元"] != "中元":
        fail(f"奇门三元 {qm['三元']}")
    else:
        ok("奇门三元中元")
    snow = qimen.build_qimen(datetime(2026, 12, 22, 12, 0))
    if snow["节气"] != "大雪":
        fail(f"奇门节气 {snow['节气']}")
    else:
        ok("奇门节气大雪")


def check_clock_on_charts() -> None:
    summer = daliuren.compute(datetime(1988, 7, 1, 12, 0))
    if summer["时间校正"]["入盘时间"] != "1988-07-01 12:00" or summer["时间校正"]["夏令时"] != "在区间，未扣":
        fail(f"夏令时未扣 {summer['时间校正']}")
    else:
        ok("1988-07-01 不确认则不扣")
    cut = daliuren.compute(datetime(1988, 7, 1, 12, 0), confirm_dst=True)
    if cut["时间校正"]["入盘时间"] != "1988-07-01 11:00":
        fail(f"夏令时已扣 {cut['时间校正']}")
    else:
        ok("1988-07-01 确认后 11:00")

    noon = daliuren.compute(datetime(2026, 11, 2, 12, 0))
    late = daliuren.compute(datetime(2026, 11, 2, 23, 30))
    if late["日干支"] != noon["日干支"] or late["时间校正"]["日界"] != "same-day":
        fail(f"默认日界 {late['日干支']} vs {noon['日干支']}")
    else:
        ok("23:30 默认与当天中午同日柱")
    nxt = daliuren.compute(datetime(2026, 11, 2, 23, 30), day_boundary="next-day")
    nxt_noon = daliuren.compute(datetime(2026, 11, 3, 12, 0))
    if nxt["日干支"] != nxt_noon["日干支"] or nxt["时间校正"]["日界"] != "next-day":
        fail(f"次日日界 {nxt['日干支']} vs {nxt_noon['日干支']}")
    else:
        ok("23:30 next-day 与次日中午同日柱")
    early = daliuren.compute(datetime(2026, 11, 3, 0, 30), day_boundary="next-day")
    if early["日干支"] != nxt_noon["日干支"]:
        fail(f"早子时被推进了次日 {early['日干支']}")
    else:
        ok("00:30 即使 next-day 仍是当天")

    moved = meihua_time.compute(datetime(2026, 7, 4, 6, 0), lon=87)
    if moved["时间校正"]["入盘时间"] == moved["时间校正"]["输入钟面"]:
        fail("经度 87 没有移动入盘时间")
    elif moved["输入"]["公历"].startswith("2026-07-04 06:00"):
        ok("经度 87 入盘时间离开 06:00，公历原文仍是钟面")
    else:
        fail(f"公历被改写 {moved['输入']['公历']}")


def check_shehai() -> None:
    # 午火临亥：亥子丑寅卯辰巳，亥水、子水克火 → 2
    # 午火临子：子丑寅卯辰巳，只有子水 → 1
    if daliuren._shehai_depth("午", "亥") != 2 or daliuren._shehai_depth("午", "子") != 1:
        fail(f"涉害深度 {_shehai_dump()}")
    else:
        ok("涉害深度 午临亥=2 午临子=1")
    winner, tie = daliuren._shehai([("午", "亥"), ("巳", "亥")])
    if winner != "午" or not tie:
        fail(f"同深应取先见午，得到 {winner} tie={tie}")
    else:
        ok("涉害同深取首见")
    # 2024-01-04 06:00 丁卯日。丑土临卯深度 1（只被卯木克），亥水临丑深度 4（丑辰未戌）。
    # 旧算法取第一个丑；新算法取亥。
    chart = daliuren.compute(datetime(2024, 1, 4, 6, 0))
    sc = chart["三传"]
    if sc["初传"] != "亥" or "被克深者" not in sc["宗门"]:
        fail(f"涉害锚点 2024-01-04 06:00 {sc}")
    else:
        ok("涉害锚点初传亥（不是旧的首见丑）")
    zeike = daliuren.compute(datetime(2026, 7, 1, 10, 0))
    if "涉害" in zeike["三传"]["宗门"]:
        fail("贼克金盘被改成涉害")
    else:
        ok("贼克金盘没有走进涉害")


def _shehai_dump() -> str:
    return f"午亥={daliuren._shehai_depth('午', '亥')} 午子={daliuren._shehai_depth('午', '子')}"


def check_special() -> None:
    # 伏吟：月将子加子时。上下同支，四课无克，仍交白卷。
    fuyin = daliuren.compute(datetime(2026, 1, 25, 0, 30))
    td = fuyin["天地盘"]
    if not all(td[z]["天盘"] == z for z in DIZHI):
        fail("2026-01-25 00:30 不是伏吟，锚点失效")
    elif fuyin["三传"]["初传"] is not None or "未实现" not in fuyin["三传"]["宗门"] or "伏吟" not in fuyin["三传"]["宗门"]:
        fail(f"伏吟无克应仍未实现 {fuyin['三传']}")
    else:
        ok("伏吟无克仍未实现")

    # 反吟：月将子加午时。三课下克上只有巳一位，应按贼克取出。
    fan = daliuren.compute(datetime(2026, 1, 25, 12, 0))
    td = fan["天地盘"]
    if not all(is_chong(z, td[z]["天盘"]) for z in DIZHI):
        fail("2026-01-25 12:00 不是反吟，锚点失效")
    else:
        sc = fan["三传"]
        if sc["初传"] != "巳" or any(sc[k] not in DIZHI for k in ("初传", "中传", "末传")) or "未实现" in sc["宗门"]:
            fail(f"反吟有克 {sc}")
        else:
            ok(f"反吟有克初传巳 宗门={sc['宗门']}")


def check_geju() -> None:
    blank = {i: {"天盘": "", "地盘": "", "八门": "", "八神": ""} for i in range(1, 10)}
    blank[1] = {"天盘": "戊", "地盘": "丙", "八门": "开", "八神": "值符"}
    names = qimen.detect_geju(blank, "死", "甲", "甲")
    if names != ["青龙返首"]:
        fail(f"合成盘青龙返首 {names}")
    else:
        ok("合成盘戊加丙 → 青龙返首")

    blank[1] = {"天盘": "丙", "地盘": "戊", "八门": "生", "八神": "九天"}
    names = qimen.detect_geju(blank, "死", "甲", "甲")
    if "飞鸟跌穴" not in names or "天遁" not in names or "青龙返首" in names:
        fail(f"合成盘天遁 {names}")
    else:
        ok("合成盘丙+戊+生门+九天 → 飞鸟跌穴、天遁")

    # 甲木克戊土
    if "五不遇时" not in qimen.detect_geju(blank, "死", "甲", "戊"):
        fail("五不遇时合成盘未报")
    else:
        ok("时干甲克日干戊 → 五不遇时")

    real = None
    absent = qimen.build_qimen(datetime(2026, 2, 24, 12, 0))
    has_pair = any(
        absent["九宫"][i]["天盘"] == "戊" and absent["九宫"][i]["地盘"] == "丙"
        for i in range(1, 10)
    )
    if has_pair != ("青龙返首" in absent["格局"]):
        fail(f"金盘青龙返首与九宫不一致 pair={has_pair} {absent['格局']}")
    elif "六仪击刑" in absent["格局"]:
        fail("不该出现六仪击刑")
    else:
        ok(f"2026-02-24 格局与九宫一致 {absent['格局'] or '无'}")

    dt = datetime(2024, 1, 1, 0, 0)
    for _ in range(400):
        chart = qimen.build_qimen(dt)
        if "青龙返首" in chart["格局"]:
            real = dt
            break
        dt += timedelta(hours=3)
    if real is None:
        fail("400 个时刻里没有青龙返首，无法核对实盘")
    else:
        ok(f"实盘青龙返首 {real.strftime('%Y-%m-%d %H:%M')}")


def main() -> int:
    try:
        clock_adjust.self_check()
        ok("clock_adjust self_check")
    except AssertionError as e:
        fail(f"clock_adjust {e}")
    check_structure()
    check_anchors()
    check_clock_on_charts()
    check_shehai()
    check_special()
    check_geju()
    print()
    if failures:
        print(f"总体 FAIL {failures}")
        return 1
    print("总体 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
