#!/usr/bin/env python3
"""将 JSON 日志渲染为人可读的 Markdown 摘要。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SYSTEM_LABEL = {"yijing": "易经", "daliuren": "大六壬", "qimen": "奇门遁甲"}
STATUS_LABEL = {
    "pending_interpretation": "待解读",
    "pending_feedback": "待反馈",
    "verified": "已验证",
}
OUTCOME_LABEL = {"hit": "应验 ✅", "miss": "未验 ❌", "partial": "部分应验 ◐", "unknown": "说不清 ·"}


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _gua_block(payload: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    inp = payload.get("输入") or {}
    if inp.get("公历"):
        lines.append(f"- **占时**：{inp['公历']}")
    if inp.get("农历"):
        lines.append(f"- **农历**：{inp['农历']}")

    ben = payload.get("本卦") or {}
    if isinstance(ben, dict) and ben.get("name"):
        seq = ben.get("sequence", "·")
        lines.append(f"- **本卦**：第 {seq} 卦 · **{ben['name']}**")
    elif isinstance(ben, dict) and ben.get("名"):
        lines.append(f"- **本卦**：**{ben['名']}**")

    bian = payload.get("变卦") or {}
    if isinstance(bian, dict) and (bian.get("name") or bian.get("名")):
        name = bian.get("name") or bian.get("名")
        lines.append(f"- **变卦**：**{name}**")

    hu = payload.get("互卦") or {}
    if isinstance(hu, dict) and (hu.get("name") or hu.get("名")):
        name = hu.get("name") or hu.get("名")
        lines.append(f"- **互卦**：**{name}**")

    if payload.get("动爻名"):
        lines.append(f"- **动爻**：{payload['动爻名']}")
    elif payload.get("动爻"):
        lines.append(f"- **动爻**：第 {payload['动爻']} 爻")

    ty = payload.get("体用") or {}
    if ty.get("体卦"):
        lines.append(
            f"- **体用**：体 {ty.get('体卦')}({ty.get('体五行', '?')}) / "
            f"用 {ty.get('用卦')}({ty.get('用五行', '?')}) → **{ty.get('生克', '')}**"
        )

    if payload.get("卦象"):
        lines.append("")
        lines.append("```")
        lines.append(str(payload["卦象"]).strip())
        lines.append("```")

    qg = payload.get("起卦方式")
    if qg:
        lines.insert(0, f"- **起卦**：{qg}")

    return lines


def _daliuren_block(payload: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if payload.get("时间"):
        lines.append(f"- **占时**：{payload['时间']}")
    if payload.get("日干支"):
        lines.append(f"- **日干支**：{payload['日干支']}  月建 {payload.get('月建', '·')}  占时 {payload.get('占时', '·')}")
    sc = payload.get("三传") or {}
    if sc:
        lines.append(
            f"- **三传**：初 {sc.get('初传', '·')} → 中 {sc.get('中传', '·')} → 末 {sc.get('末传', '·')}（{sc.get('宗门', '')}）"
        )
    return lines


def _qimen_block(payload: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if payload.get("时间"):
        lines.append(f"- **占时**：{payload['时间']}")
    if payload.get("局"):
        lines.append(f"- **局**：{payload['局']}")
    if payload.get("值符星"):
        lines.append(f"- **值符 / 值使**：{payload['值符星']} / {payload.get('值使门', '·')}")
    return lines


def _liuyao_block(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    ben = data.get("本卦") or {}
    if ben.get("名"):
        lines.append(f"- **本卦**：{ben['名']}（{data.get('八宫', '')}宫）")
    lines.append(f"- **世应**：世 {data.get('世爻', '·')} · 应 {data.get('应爻', '·')}")
    if data.get("动爻"):
        lines.append(f"- **动爻**：{data['动爻']}")
    ys = data.get("用神提示") or {}
    if ys.get("用神"):
        lines.append(f"- **用神**：{ys['用神']} — {ys.get('说明', '')}")
    rz = data.get("日干支") or {}
    if rz.get("日干支"):
        lines.append(f"- **日辰**：{rz['日干支']}  旬空 {'、'.join(rz.get('旬空', []))}  月建 {rz.get('月建', '·')}")
    liuyao = data.get("六爻") or []
    if liuyao:
        lines.append("")
        lines.append("| 爻 | 地支 | 六亲 | 旺衰 | 标记 |")
        lines.append("|----|------|------|------|------|")
        for ln in liuyao:
            flags = []
            if ln.get("世"):
                flags.append("世")
            if ln.get("应"):
                flags.append("应")
            if ln.get("动"):
                flags.append("动")
            if ln.get("旬空"):
                flags.append("空")
            if ln.get("月破"):
                flags.append("月破")
            if ln.get("暗动日破"):
                flags.append(str(ln["暗动日破"]))
            lines.append(
                f"| {ln.get('爻名', ln.get('爻位', ''))} | {ln.get('地支', '')} | "
                f"{ln.get('六亲', '')} | {ln.get('旺衰', '')} | {' '.join(flags)} |"
            )
    return lines


def render_session_markdown(session_id: str, records_dir: Path) -> str:
    sdir = records_dir / session_id
    meta = _read_json(sdir / "meta.json") or {}
    payload = _read_json(sdir / "payload.json") or {}
    liuyao = _read_json(sdir / "liuyao_pan.json")

    system = meta.get("system", "")
    sys_label = SYSTEM_LABEL.get(system, system)
    status = STATUS_LABEL.get(meta.get("status", ""), meta.get("status", ""))
    question = meta.get("question") or "（未填写问事）"
    interp = meta.get("interpretation") or {}
    fb = meta.get("feedback")

    lines = [
        f"# 占卜记录 · {session_id}",
        "",
        "## 概览",
        "",
        "| 项目 | 内容 |",
        "|------|------|",
        f"| 体系 | {sys_label} |",
        f"| 问事 | {question} |",
        f"| 方法 | {meta.get('method', '·')} |",
        f"| 状态 | {status} |",
        f"| 记录时间 | {meta.get('created_at', '·')} |",
    ]
    if meta.get("datetime"):
        lines.append(f"| 占时 | {meta['datetime']} |")
    lines.append("")

    if payload:
        lines.append("## 排盘摘要")
        lines.append("")
        if system == "yijing":
            lines.extend(_gua_block(payload))
        elif system == "daliuren":
            lines.extend(_daliuren_block(payload))
        elif system == "qimen":
            lines.extend(_qimen_block(payload))
        else:
            lines.append("- （见 `payload.json`）")
        lines.append("")

    if liuyao:
        lines.append("## 六爻装卦")
        lines.append("")
        lines.extend(_liuyao_block(liuyao))
        lines.append("")

    if interp.get("verdict") or interp.get("summary"):
        lines.append("## 解读")
        lines.append("")
        if interp.get("verdict"):
            lines.append(f"- **倾向**：{interp['verdict']}")
        if interp.get("summary"):
            lines.append(f"- **摘要**：{interp['summary']}")
        lines.append("")

    if fb:
        lines.append("## 事后反馈")
        lines.append("")
        outcome = OUTCOME_LABEL.get(fb.get("outcome", ""), fb.get("outcome", ""))
        lines.append(f"- **结果**：{outcome}")
        if fb.get("note"):
            lines.append(f"- **说明**：{fb['note']}")
        lines.append(f"- **反馈时间**：{fb.get('received_at', '·')}")
        lines.append("")

    lines.append("## 原始数据")
    lines.append("")
    lines.append("- `meta.json` — 索引与状态")
    lines.append("- `payload.json` — 排盘 JSON")
    if liuyao:
        lines.append("- `liuyao_pan.json` — 六爻装卦")
    if (sdir / "interpretation.json").is_file():
        lines.append("- `interpretation.json`")
    if (sdir / "feedback.json").is_file():
        lines.append("- `feedback.json`")
    lines.append("")

    return "\n".join(lines)


def render_index_markdown(records_dir: Path, session_ids: list[str], metas: list[dict[str, Any]]) -> str:
    lines = [
        "# 卦理日志索引",
        "",
        "按时间倒序；点进各目录下的 **README.md** 查看可读摘要。",
        "",
        "| id | 时间 | 体系 | 问事 | 倾向 | 状态 |",
        "|----|------|------|------|------|------|",
    ]
    for sid, meta in zip(session_ids, metas):
        sys_label = SYSTEM_LABEL.get(meta.get("system", ""), meta.get("system", ""))
        verdict = (meta.get("interpretation") or {}).get("verdict") or "·"
        status = STATUS_LABEL.get(meta.get("status", ""), meta.get("status", ""))
        q = (meta.get("question") or "·")[:24]
        t = (meta.get("created_at") or "")[:16]
        lines.append(f"| [{sid}]({sid}/README.md) | {t} | {sys_label} | {q} | {verdict} | {status} |")
    lines.append("")
    return "\n".join(lines)
