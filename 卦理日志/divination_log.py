#!/usr/bin/env python3
"""
卦理日志 CLI — 配合起卦脚本自动落盘；解读 amend、反馈 feedback。

目录结构（每次占卜一个文件夹，自动创建）：
  skills/卦理日志/records/<YYYYMMDD_NNN>/
    meta.json          # 问事、倾向、状态
    payload.json       # 起卦脚本 JSON
    interpretation.json  # Agent 解读后（amend）
    feedback.json      # 用户反馈后
    liuyao_pan.json    # 可选，六爻装卦追加

用法：
  py -3 divination_log.py amend --latest --question "..." --verdict "中性偏吉" --summary "..."
  py -3 divination_log.py feedback --latest --outcome hit --note "..."
  py -3 divination_log.py list --pending
  py -3 divination_log.py show --id 20260704_001
  py -3 divination_log.py render --all    # 补生成可读 README.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import session_log


def read_json_file(path: Path) -> dict[str, Any] | list[Any]:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        text = raw.decode("utf-16")
    else:
        text = raw.decode("utf-8-sig")
    return json.loads(text)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="卦理日志：解读 amend / 反馈 feedback / 查询")
    sub = parser.add_subparsers(dest="command", required=True)

    p_amend = sub.add_parser("amend", help="解读完成后补充问事、倾向、摘要")
    p_amend.add_argument("--id", help="记录 id")
    p_amend.add_argument("--latest", action="store_true", help="最近一条待解读/待反馈")
    p_amend.add_argument("--question", help="用户问事")
    p_amend.add_argument("--verdict", help="解读倾向")
    p_amend.add_argument("--summary", help="一句话断语")
    p_amend.set_defaults(func="amend")

    p_fb = sub.add_parser("feedback", help="用户事后反馈")
    p_fb.add_argument("--id")
    p_fb.add_argument("--latest", action="store_true")
    p_fb.add_argument(
        "--outcome",
        required=True,
        choices=["hit", "miss", "partial", "unknown"],
    )
    p_fb.add_argument("--note", default="")
    p_fb.set_defaults(func="feedback")

    p_list = sub.add_parser("list", help="列出记录")
    p_list.add_argument("--system", choices=["yijing", "daliuren", "qimen"])
    p_list.add_argument("--pending", action="store_true", help="仅待反馈")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.set_defaults(func="list")

    p_show = sub.add_parser("show", help="查看单条")
    p_show.add_argument("--id", required=True)
    p_show.set_defaults(func="show")

    p_render = sub.add_parser("render", help="生成/刷新人类可读 README.md")
    p_render.add_argument("--id", help="单条记录 id")
    p_render.add_argument("--all", action="store_true", help="全部记录")
    p_render.set_defaults(func="render")

    # 兼容：手动 record（脚本未跑时补救）
    p_rec = sub.add_parser("record", help="手动写入（通常不必，脚本已自动落盘）")
    p_rec.add_argument("--system", required=True, choices=["yijing", "daliuren", "qimen"])
    p_rec.add_argument("--question", default="")
    p_rec.add_argument("--method", default="")
    p_rec.add_argument("--datetime", default="")
    p_rec.add_argument("--payload", required=True)
    p_rec.add_argument("--verdict", default="")
    p_rec.add_argument("--summary", default="")
    p_rec.set_defaults(func="record")

    args = parser.parse_args()

    if args.command == "amend":
        if not args.id and not args.latest:
            parser.error("amend 需 --id 或 --latest")
        if args.id:
            sid = args.id
        else:
            sid = session_log.find_session(None, latest=True)
        out = session_log.amend_session(
            sid,
            question=args.question,
            verdict=args.verdict,
            summary=args.summary,
        )
        print(json.dumps({"ok": True, **out}, ensure_ascii=False))

    elif args.command == "feedback":
        if not args.id and not args.latest:
            parser.error("feedback 需 --id 或 --latest")
        if args.id:
            sid = args.id
        else:
            try:
                sid = session_log.find_session(None, pending_feedback=True)
            except FileNotFoundError:
                sid = session_log.find_session(None, latest=True)
        out = session_log.add_feedback(sid, outcome=args.outcome, note=args.note)
        print(json.dumps({"ok": True, **out}, ensure_ascii=False))

    elif args.command == "list":
        rows = session_log.list_sessions(
            system=args.system,
            pending_feedback=args.pending,
            limit=args.limit,
        )
        print(json.dumps(rows, ensure_ascii=False, indent=2))

    elif args.command == "show":
        print(json.dumps(session_log.load_session_full(args.id), ensure_ascii=False, indent=2))

    elif args.command == "render":
        if args.all:
            ids = session_log.render_all_human_views()
            print(json.dumps({"ok": True, "rendered": ids}, ensure_ascii=False, indent=2))
        elif args.id:
            session_log.refresh_human_view(args.id)
            print(json.dumps({"ok": True, "id": args.id}, ensure_ascii=False))
        else:
            parser.error("render 需 --id 或 --all")

    elif args.command == "record":
        payload = read_json_file(Path(args.payload))
        created = session_log.create_session(
            system=args.system,
            method=args.method,
            payload=payload,
            datetime_str=args.datetime,
            question=args.question,
        )
        if args.verdict or args.summary:
            session_log.amend_session(
                created["id"],
                question=args.question or None,
                verdict=args.verdict or None,
                summary=args.summary or None,
            )
        print(json.dumps({"ok": True, **created}, ensure_ascii=False))


if __name__ == "__main__":
    main()
