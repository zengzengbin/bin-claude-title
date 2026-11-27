#!/usr/bin/env python3
"""UserPromptSubmit hook: periodically ask the main agent to review/update the
desktop session title (via mcp__ccd_session_mgmt__set_session_title).
Pause: create ~/.claude/hooks/bin-title/paused ; pin a session: create state/<sid>.pinned"""
import glob, json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state")

SHORT = ("[话题自动命名 · 静默任务] 当前标题：{title}。仅当用户已明确转向新主线、或标题与主线明显不符时，"
         "才用 mcp__ccd_session_mgmt__set_session_title（session_id=\"self\"）按原格式「emoji 对象｜目标」改一次；"
         "否则什么都不做。不要向用户提及此任务。")


def find_session(cli_sid):
    root = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Claude-Data")
    for p in glob.glob(os.path.join(root, "*", "claude-code-sessions", "*", "*", "local_*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        if d.get("cliSessionId") == cli_sid:
            return d
    return {}


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
    info = find_session(sid)
    # whitelist: only top-level desktop sessions. Unknown (no session file: headless/subagent)
    # and branch/side-chat sessions (forked / spawned / btw) are skipped.
    if not info or any(k in info for k in ("forkedFromSessionId", "spawnedFrom", "btwLoweredFrom")):
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
    title = info.get("title") or ""
    formatted = "｜" in title
    if not ((n <= 3 and not formatted) or n % 8 == 0):
        return
    if formatted:
        rules = SHORT.replace("{title}", title)
    else:
        with open(os.path.join(BASE, "naming_rules.md"), encoding="utf-8") as f:
            rules = f.read().replace("{title}", title or "（未知）")
    out = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": rules}}
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))


main()
