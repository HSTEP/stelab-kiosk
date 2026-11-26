#!/usr/bin/env python3
"""Publish live Antigravity + ChatGPT (Codex) + AI_HANDOFF.md status to Home Assistant."""

import json
import os
import re
import sqlite3
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AGY_DB = Path("/config/chatgpt/home/.gemini/antigravity-cli/conversation_summaries.db")
CODEX_DB = Path("/config/chatgpt/home/.codex/state_5.sqlite")
HANDOFF_MD = Path("/config/chatgpt/home/AI_HANDOFF.md")
TOKEN_FILE = Path("/run/s6/container_environment/SUPERVISOR_TOKEN")
ENTITY_URL = "http://supervisor/core/api/states/sensor.stelab_ai_agents"


def iso_age_sec(iso_str: str) -> float:
    try:
        s = iso_str.replace("Z", "+00:00").replace(" ", "T")
        # Truncate sub-microsecond precision if present (e.g. 9 digits)
        s = re.sub(r"(\.\d{6})\d+", r"\1", s)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds())
    except Exception:
        return 1e9


def read_antigravity() -> list[dict]:
    items = []
    if not AGY_DB.exists():
        return items
    try:
        con = sqlite3.connect(f"file:{AGY_DB}?mode=ro", uri=True, timeout=2)
        rows = con.execute(
            """
            SELECT conversation_id, title, status, step_count, last_modified_time, not_fully_idle
            FROM conversation_summaries
            WHERE killed = 0 AND step_count > 0
            ORDER BY last_modified_time DESC
            LIMIT 8
            """
        ).fetchall()
        con.close()
        for cid, title, status, steps, lmt, not_idle in rows:
            age = iso_age_sec(str(lmt))
            st_upper = (status or "").upper()
            if "WAITING" in st_upper or "APPROVAL" in st_upper or "USER" in st_upper:
                norm = "waiting"
                detail = f"Čeká na potvrzení · {steps} kroků"
            elif ("RUNNING" in st_upper or not_idle) and age < 180:
                norm = "running"
                detail = f"Pracuje · {steps} kroků"
            else:
                norm = "idle"
                detail = f"Klid · {steps} kroků"
            items.append({
                "agent": "Antigravity",
                "id": cid[:8],
                "title": title or f"Konverzace {cid[:8]}",
                "status": norm,
                "raw_status": status,
                "age_sec": int(age),
                "updated_at": str(lmt)[:19],
                "detail": detail,
            })
    except Exception as e:
        items.append({
            "agent": "Antigravity",
            "id": "err",
            "title": "Chyba čtení DB",
            "status": "idle",
            "age_sec": 0,
            "updated_at": "",
            "detail": str(e)[:100],
        })
    return items


def check_codex_rollout_waiting(path_str: str) -> tuple[bool, str]:
    """Inspect tail of Codex rollout jsonl to detect unanswered user input / approval request."""
    try:
        p = Path(path_str)
        if not p.exists():
            return False, ""
        size = p.stat().st_size
        with p.open("rb") as f:
            f.seek(max(0, size - 32768))
            tail = f.read().decode("utf-8", "ignore")
        lines = [ln for ln in tail.splitlines() if ln.strip()]
        pending_q = ""
        for ln in lines[-40:]:
            if "request_user_input_async" in ln and "send_user_message_question_reply" not in ln:
                try:
                    d = json.loads(ln)
                    payload = d.get("payload", {})
                    if payload.get("type") in ("function_call", "custom_tool_call") or "question" in ln:
                        m = re.search(r'"question"\s*:\s*"([^"]{5,120})"', ln)
                        pending_q = m.group(1) if m else "Čeká na odpověď / potvrzení"
                except Exception:
                    pass
            elif "send_user_message_question_reply" in ln or '"role":"user"' in ln:
                pending_q = ""
        return bool(pending_q), pending_q
    except Exception:
        return False, ""


def read_codex() -> list[dict]:
    items = []
    if not CODEX_DB.exists():
        return items
    try:
        con = sqlite3.connect(f"file:{CODEX_DB}?mode=ro", uri=True, timeout=2)
        rows = con.execute(
            """
            SELECT id, COALESCE(NULLIF(name,''), NULLIF(title,''), 'Codex') AS label,
                   rollout_path, updated_at, model, reasoning_effort
            FROM threads
            WHERE archived = 0 AND COALESCE(thread_source, '') != 'guardian_review'
            ORDER BY updated_at DESC
            LIMIT 8
            """
        ).fetchall()
        con.close()
        now_ts = time.time()
        for tid, label, rpath, upd_ts, model, effort in rows:
            age = max(0, int(now_ts - float(upd_ts or 0)))
            waiting, q_text = (False, "")
            if age < 86400 and rpath:
                waiting, q_text = check_codex_rollout_waiting(rpath)
            if waiting:
                norm = "waiting"
                detail = f"Čeká na potvrzení: {q_text}"
            elif age < 45:
                norm = "running"
                detail = f"Pracuje ({model or 'Codex'})"
            else:
                norm = "idle"
                mins = age // 60
                ago = f"{mins} min" if mins < 120 else f"{mins // 60} h"
                detail = f"Klid · naposledy před {ago}"
            dt_str = datetime.fromtimestamp(float(upd_ts or 0), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            items.append({
                "agent": "ChatGPT (Codex)",
                "id": tid[:8],
                "title": label,
                "status": norm,
                "age_sec": age,
                "updated_at": dt_str,
                "detail": detail,
            })
    except Exception as e:
        items.append({
            "agent": "ChatGPT (Codex)",
            "id": "err",
            "title": "Chyba čtení DB",
            "status": "idle",
            "age_sec": 0,
            "updated_at": "",
            "detail": str(e)[:100],
        })
    return items


def read_handoff() -> dict:
    res = {"tasks": [], "locks": [], "questions": []}
    if not HANDOFF_MD.exists():
        return res
    section = None
    for line in HANDOFF_MD.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if s.startswith("## "):
            h = s[3:].lower()
            if "aktivn" in h:
                section = "tasks"
            elif "zámk" in h or "upravovan" in h:
                section = "locks"
            elif "porada" in h or "second opinion" in h:
                section = "questions"
            else:
                section = None
        elif section and s.startswith("- ") and not s.startswith("- _("):
            clean = re.sub(r"\*\*|`", "", s[2:]).strip()
            res[section].append(clean[:140])
    return res


def publish_once() -> dict:
    agents = read_antigravity() + read_codex()
    handoff = read_handoff()
    waiting = [a for a in agents if a["status"] == "waiting"]
    running = [a for a in agents if a["status"] == "running"]

    if waiting:
        state = f"Čeká na potvrzení ({len(waiting)})"
    elif running:
        state = f"Pracuje ({len(running)})"
    else:
        state = "Klid"

    payload = {
        "state": state,
        "attributes": {
            "friendly_name": "STELAB AI Agenti",
            "icon": "mdi:robot-outline",
            "running_count": len(running),
            "waiting_count": len(waiting),
            "waiting_summary": "; ".join(f"{a['agent']}: {a['title']}" for a in waiting)[:250],
            "agents": agents[:12],
            "handoff_tasks": handoff["tasks"][:8],
            "handoff_locks": handoff["locks"][:5],
            "handoff_questions": handoff["questions"][:5],
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }
    tok = TOKEN_FILE.read_text().strip()
    req = urllib.request.Request(
        ENTITY_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()
    return payload


if __name__ == "__main__":
    import sys
    if "--once" in sys.argv:
        p = publish_once()
        print(json.dumps(p, ensure_ascii=False, indent=2))
    else:
        while True:
            try:
                publish_once()
            except Exception as exc:
                print(f"[ai_agents_monitor] error: {exc}", flush=True)
            time.sleep(15)
