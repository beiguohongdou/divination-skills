"""起卦脚本共用：成功排盘后自动写入卦理日志（任意 Agent 跑脚本即落盘）。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_DIV_ROOT = Path(__file__).resolve().parent
# 优先仓库内卦理日志；兼容旧布局 skills/卦理日志（与 divination-skills 并列）
_LOG_LIB = _DIV_ROOT / "卦理日志"
if not _LOG_LIB.is_dir():
    _LOG_LIB = _DIV_ROOT.parent / "卦理日志"


def attach_session_log(
    *,
    system: str,
    method: str,
    payload: dict[str, Any] | list[Any],
    datetime_str: str = "",
    question: str = "",
    script: str = "",
    log_id: str | None = None,
    extra_filename: str | None = None,
) -> dict[str, Any] | None:
    if os.environ.get("DIVINATION_NO_LOG", "").strip() == "1":
        return None
    if not _LOG_LIB.is_dir():
        # 新用户无目录时由 session_log 自动创建 records/
        pass
    try:
        if str(_LOG_LIB) not in sys.path:
            sys.path.insert(0, str(_LOG_LIB))
        import session_log  # noqa: WPS433

        if log_id:
            if extra_filename:
                session_log.append_payload_file(log_id, extra_filename, payload)
            return {"id": log_id, "dir": str(session_log.session_dir(log_id)), "appended": extra_filename}

        return session_log.create_session(
            system=system,
            method=method,
            payload=payload,
            datetime_str=datetime_str,
            question=question,
            script=script or method,
        )
    except Exception:
        return None


def inject_log_into_result(result: dict[str, Any], log_info: dict[str, Any] | None) -> dict[str, Any]:
    if log_info:
        result["_session_log"] = log_info
    return result
