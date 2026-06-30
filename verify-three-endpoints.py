#!/usr/bin/env python3
"""三端 junction 联调抽检：从 Cursor / Claude / Hanako 挂载点各跑同一锚点起卦。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ANCHOR_DATE = "2026-07-04"
ANCHOR_TIME = "06:00"
ANCHOR = f"{ANCHOR_DATE} {ANCHOR_TIME}"

EXPECTED = {
    "ben": "地雷复",
    "nian": 7,
    "bian": "山雷颐",
    "shengke": "体克用",
}

ENDPOINTS = [
    ("Cursor (.agents)", Path(r"E:\HanakoWorkSpace\.agents\skills\yijing-divination")),
    ("Claude", Path.home() / ".claude" / "skills" / "yijing-divination"),
    ("Hanako", Path.home() / ".hanako" / "skills" / "yijing-divination"),
]

STANDARD_PROMPT = f"""请用梅花易数时间起卦：公历 {ANCHOR}，问「今日运势如何」。
要求：必须先运行 meihua_time.py（禁止心算）；解读前先给 6 行摘要。"""


def run_meihua(scripts_dir: Path) -> dict:
    cmd = [sys.executable, "meihua_time.py", ANCHOR_DATE, ANCHOR_TIME, "--json"]
    out = subprocess.check_output(cmd, cwd=scripts_dir, text=True, encoding="utf-8")
    return json.loads(out)


def check_endpoint(name: str, root: Path) -> tuple[bool, str, dict | None]:
    meihua = root / "scripts" / "meihua_time.py"
    if not meihua.is_file():
        return False, f"missing {meihua}", None
    try:
        data = run_meihua(root / "scripts")
    except Exception as e:
        return False, str(e), None

    ben = data["本卦"]["name"]
    nian = int(data["取数"]["年数"]["值"])
    bian = data["变卦"]["name"]
    sk = data["体用"]["生克"]
    ok = (
        ben == EXPECTED["ben"]
        and nian == EXPECTED["nian"]
        and bian == EXPECTED["bian"]
        and sk == EXPECTED["shengke"]
    )
    detail = f"本卦={ben} 年数={nian} 变卦={bian} 体用={sk}"
    return ok, detail, data


def main() -> int:
    print("=== 三端 junction 脚本联调（锚点:", ANCHOR, "）===\n")
    print("【标准 UI 抽检 prompt】（复制到 Cursor / Claude / Hanako 各测一遍）")
    print(STANDARD_PROMPT)
    print()

    all_ok = True
    for name, root in ENDPOINTS:
        ok, msg, _ = check_endpoint(name, root)
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"{name:20} {status:4}  {msg}")

    print()
    print(
        "期望:",
        f"本卦={EXPECTED['ben']}",
        f"年数={EXPECTED['nian']}",
        f"变卦={EXPECTED['bian']}",
        f"体用={EXPECTED['shengke']}",
    )

    # 跨 skill 路径
    yijing_scripts = ENDPOINTS[0][1] / "scripts"
    div_root = yijing_scripts.parent.parent
    daliuren = div_root / "daliuren-divination" / "scripts" / "daliuren.py"
    qimen = div_root / "qimen-dunjia" / "scripts" / "qimen.py"
    print("\n=== 跨 skill 路径抽检 ===")
    for label, script in [("daliuren", daliuren), ("qimen", qimen)]:
        if not script.is_file():
            print(f"{label}: FAIL missing {script}")
            all_ok = False
            continue
        try:
            subprocess.check_output(
                [sys.executable, str(script), "--json", ANCHOR_DATE, ANCHOR_TIME],
                text=True,
                encoding="utf-8",
            )
            print(f"{label}: PASS")
        except Exception as e:
            print(f"{label}: FAIL {e}")
            all_ok = False

    print()
    if all_ok:
        print("总体: PASS（脚本层三端一致）")
        print("UI 层请在三端各粘贴上方标准 prompt，人工确认 Agent 是否跑脚本且卦象一致。")
        return 0
    print("总体: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
