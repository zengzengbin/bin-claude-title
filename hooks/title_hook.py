#!/usr/bin/env python3
"""UserPromptSubmit hook: periodically ask the main agent to review/update the
desktop session title (via mcp__ccd_session_mgmt__set_session_title).
Pause: create ~/.claude/hooks/binbin-title/paused ; pin a session: create state/<sid>.pinned"""
import glob, json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state")


def current_title(cli_sid):
    root = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Claude-Data")
    for p in glob.glob(os.path.join(root, "*", "claude-code-sessions", "*", "*", "local_*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        if d.get("cliSessionId") == cli_sid:
            return d.get("title") or ""
    return ""


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    sid = data.get("session_id")
    if not sid or os.environ.get("OIL_TITLE_WORKER"):
        return
    if os.path.exists(os.path.join(BASE, "paused")) or os.path.exists(os.path.join(STATE, sid + ".pinned")):
        return
    os.makedirs(STATE, exist_ok=True)
    sp = os.path.join(STATE, sid + ".json")
    try:
        with open(sp, encoding="utf-8") as f:
            n = json.load(f).get("n", 0)
    except Exception:
        n = 0
    n += 1
    with open(sp, "w", encoding="utf-8") as f:
        json.dump({"n": n}, f)
    title = current_title(sid)
    formatted = "｜" in title
    if not ((n <= 3 and not formatted) or n % 4 == 0):
        return
    with open(os.path.join(BASE, "naming_rules.md"), encoding="utf-8") as f:
        rules = f.read().replace("{title}", title or "（未知）")
    out = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": rules}}
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))


main()
