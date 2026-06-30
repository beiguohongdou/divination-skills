#!/usr/bin/env python3
"""
卦理日志核心库 — 每次占卜一个目录：records/<id>/{meta.json,payload.json,...}

目录不存在时自动创建（新用户 clone 后首次起卦即可用）。
环境变量 DIVINATION_NO_LOG=1 可关闭自动写入（调试用）。
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

LOG_DIR = Path(__file__).resolve().parent
RECORDS_DIR = LOG_DIR / "records"
TZ_CN = timezone(timedelta(hours=8))

from summary_render import render_index_markdown, render_session_markdown  # noqa: E402

STATUS_PENDING_INTERP = "pending_interpretation"
STATUS_PENDING_FEEDBACK = "pending_feedback"
STATUS_VERIFIED = "verified"


def logging_enabled() -> bool:
    return os.environ.get("DIVINATION_NO_LOG", "").strip() != "1"


def now_iso() -> str:
    return datetime.now(TZ_CN).isoformat(timespec="seconds")


def ensure_records_dir() -> Path:
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    return RECORDS_DIR


def session_dir(session_id: str) -> Path:
    return RECORDS_DIR / session_id


def meta_path(session_id: str) -> Path:
    return session_dir(session_id) / "meta.json"


def load_meta(session_id: str) -> dict[str, Any]:
    p = meta_path(session_id)
    if not p.is_file():
        raise FileNotFoundError(f"未找到记录 id={session_id}")
    return json.loads(p.read_text(encoding="utf-8"))


def save_meta(session_id: str, meta: dict[str, Any]) -> None:
    meta["updated_at"] = now_iso()
    meta_path(session_id).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    refresh_human_view(session_id)


def refresh_human_view(session_id: str) -> None:
    """生成 records/<id>/README.md 与总索引。"""
    try:
        (session_dir(session_id) / "README.md").write_text(
            render_session_markdown(session_id, RECORDS_DIR),
            encoding="utf-8",
        )
        refresh_records_index()
    except Exception:
        pass


def refresh_records_index() -> None:
    ids = list_session_ids()
    if not ids:
        return
    metas = [load_meta(sid) for sid in reversed(ids)]
    rev_ids = list(reversed(ids))
    (RECORDS_DIR / "README.md").write_text(
        render_index_markdown(RECORDS_DIR, rev_ids, metas),
        encoding="utf-8",
    )


def render_all_human_views() -> list[str]:
    """为已有记录补生成 README（升级后一次性调用）。"""
    done: list[str] = []
    for sid in list_session_ids():
        refresh_human_view(sid)
        done.append(sid)
    return done


def list_session_ids() -> list[str]:
    if not RECORDS_DIR.is_dir():
        return []
    ids = []
    for p in RECORDS_DIR.iterdir():
        if p.is_dir() and (p / "meta.json").is_file():
            ids.append(p.name)
    return sorted(ids)


def next_id() -> str:
    ensure_records_dir()
    day = datetime.now(TZ_CN).strftime("%Y%m%d")
    prefix = f"{day}_"
    nums: list[int] = []
    for sid in list_session_ids():
        if sid.startswith(prefix):
            try:
                nums.append(int(sid.split("_", 1)[1]))
            except ValueError:
                pass
    return f"{day}_{max(nums, default=0) + 1:03d}"


def create_session(
    *,
    system: str,
    method: str,
    payload: dict[str, Any] | list[Any],
    datetime_str: str = "",
    question: str = "",
    script: str = "",
) -> dict[str, Any]:
    """起卦脚本成功输出后调用；自动建目录写 payload。"""
    ensure_records_dir()
    sid = next_id()
    sdir = session_dir(sid)
    sdir.mkdir(parents=True, exist_ok=True)

    meta: dict[str, Any] = {
        "id": sid,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "system": system,
        "method": method,
        "script": script,
        "datetime": datetime_str,
        "question": question,
        "interpretation": {"verdict": "", "summary": ""},
        "feedback": None,
        "status": STATUS_PENDING_INTERP if not question else STATUS_PENDING_FEEDBACK,
        "dir": str(sdir),
    }
    meta_path(sid).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (sdir / "payload.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    refresh_human_view(sid)
    return {"id": sid, "dir": str(sdir), "status": meta["status"]}


def append_payload_file(session_id: str, filename: str, payload: dict[str, Any] | list[Any]) -> None:
    """同一占断的补充脚本（如 liuyao_pan）可写入同目录额外文件。"""
    sdir = session_dir(session_id)
    if not sdir.is_dir():
        raise FileNotFoundError(f"未找到目录 id={session_id}")
    (sdir / filename).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    meta = load_meta(session_id)
    extras = meta.setdefault("extra_payloads", [])
    if filename not in extras:
        extras.append(filename)
    save_meta(session_id, meta)


def amend_session(
    session_id: str,
    *,
    question: str | None = None,
    verdict: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    meta = load_meta(session_id)
    if question is not None:
        meta["question"] = question
    interp = meta.setdefault("interpretation", {})
    if verdict is not None:
        interp["verdict"] = verdict
    if summary is not None:
        interp["summary"] = summary
    if meta.get("question") and (interp.get("verdict") or interp.get("summary")):
        meta["status"] = STATUS_PENDING_FEEDBACK
    (session_dir(session_id) / "interpretation.json").write_text(
        json.dumps(meta["interpretation"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    save_meta(session_id, meta)
    return {"id": session_id, "status": meta["status"]}


def add_feedback(
    session_id: str,
    *,
    outcome: str,
    note: str = "",
) -> dict[str, Any]:
    meta = load_meta(session_id)
    fb = {
        "received_at": now_iso(),
        "outcome": outcome,
        "note": note,
    }
    meta["feedback"] = fb
    meta["status"] = STATUS_VERIFIED
    (session_dir(session_id) / "feedback.json").write_text(
        json.dumps(fb, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    save_meta(session_id, meta)
    return {"id": session_id, "outcome": outcome}


def find_session(session_id: str | None, *, latest: bool = False, pending_feedback: bool = False) -> str:
    if session_id:
        if not meta_path(session_id).is_file():
            raise FileNotFoundError(f"未找到记录 id={session_id}")
        return session_id
    ids = list_session_ids()
    for sid in reversed(ids):
        meta = load_meta(sid)
        if pending_feedback and meta.get("status") == STATUS_PENDING_FEEDBACK:
            return sid
        if latest and meta.get("status") != STATUS_VERIFIED:
            return sid
    raise FileNotFoundError("没有匹配的记录")


def list_sessions(
    *,
    system: str | None = None,
    pending_feedback: bool = False,
    limit: int = 20,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sid in reversed(list_session_ids()):
        meta = load_meta(sid)
        if system and meta.get("system") != system:
            continue
        if pending_feedback and meta.get("status") != STATUS_PENDING_FEEDBACK:
            continue
        rows.append(
            {
                "id": sid,
                "created_at": meta.get("created_at"),
                "system": meta.get("system"),
                "question": meta.get("question"),
                "verdict": (meta.get("interpretation") or {}).get("verdict"),
                "status": meta.get("status"),
                "dir": meta.get("dir"),
            }
        )
        if len(rows) >= limit:
            break
    return rows


def load_session_full(session_id: str) -> dict[str, Any]:
    meta = load_meta(session_id)
    sdir = session_dir(session_id)
    out: dict[str, Any] = {"meta": meta}
    for name in ("payload.json", "interpretation.json", "feedback.json"):
        p = sdir / name
        if p.is_file():
            out[name.replace(".json", "")] = json.loads(p.read_text(encoding="utf-8"))
    for extra in meta.get("extra_payloads", []):
        p = sdir / extra
        if p.is_file():
            out.setdefault("extra", {})[extra] = json.loads(p.read_text(encoding="utf-8"))
    return out
