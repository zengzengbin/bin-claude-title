#!/usr/bin/env python3
"""UserPromptSubmit hook: periodically ask the main agent to review/update the
desktop session title (via mcp__ccd_session_mgmt__set_session_title).
Pause: create ~/.claude/hooks/bin-title/paused ; pin a session: create state/<sid>.pinned
Log: state/inject.log (JSON lines, rotated to inject.log.1 past LOG_MAX bytes)"""
import glob, json, os, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state")
LOG = os.path.join(STATE, "inject.log")
LOG_MAX = 256 * 1024        # rotate past this size; at most two files (~512 KB) kept
STATE_TTL = 30 * 86400      # per-session counters idle this long are pruned
EVERY = 8                   # periodic review interval (turns)
GRACE = 3                   # wait at most this many turns for a light turn
LIGHT = 20                  # a prompt this short (chars) counts as a light turn

SHORT = ("[话题自动命名 · 静默任务] 先完整处理本轮用户请求，全部完成后再做这件事：当前标题：{title}。"
         "仅当用户已明确转向新主线、或标题与主线明显不符时，才用 mcp__ccd_session_mgmt__set_session_title"
         "（session_id=\"self\"）按原格式「emoji 对象｜目标」改一次；否则什么都不做。不要向用户提及此任务。")
RETRY = ("[话题自动命名 · 静默任务] 先完整处理本轮用户请求，全部完成后再做这件事：当前标题：{title}，"
         "仍不是「emoji 对象｜目标」格式。若主线已明确，按此前注入的命名规则用 mcp__ccd_session_mgmt__set_session_title"
         "（session_id=\"self\"）改一次；信息仍不足则不改。不要向用户提及此任务。")


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


def prune_state():
    cutoff = time.time() - STATE_TTL
    for p in glob.glob(os.path.join(STATE, "*.json")):
        try:
            if os.path.getmtime(p) < cutoff:
                os.remove(p)
        except OSError:
            pass


def log(sid, n, kind, chars):
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) > LOG_MAX:
            os.replace(LOG, LOG + ".1")
        rec = {"t": time.strftime("%Y-%m-%d %H:%M:%S"), "sid": sid, "n": n, "kind": kind, "chars": chars}
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


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
            st = json.load(f)
    except Exception:
        st = {}
    n = st.get("n", 0) + 1
    if n == 1:
        prune_state()
    title = info.get("title") or ""
    formatted = "｜" in title
    light = len((data.get("prompt") or "").strip()) <= LIGHT

    kind = None
    if not formatted and n <= 3:
        # naming early: full rules once, a short reminder on the next turns
        kind = "retry" if st.get("full") else "full"
    else:
        if n % EVERY == 0 and st.get("due") is None:
            st["due"] = n
        due = st.get("due")
        # periodic review waits for a light turn (e.g. "继续"), forced after GRACE turns
        if due is not None and (light or n - due >= GRACE):
            kind = "review" if formatted else "full"
            st["due"] = None

    if kind == "full":
        with open(os.path.join(BASE, "naming_rules.md"), encoding="utf-8") as f:
            rules = f.read().replace("{title}", title or "（未知）")
        st["full"] = True
    elif kind == "retry":
        rules = RETRY.replace("{title}", title or "（未知）")
    elif kind == "review":
        rules = SHORT.replace("{title}", title)

    st["n"] = n
    with open(sp, "w", encoding="utf-8") as f:
        json.dump(st, f)
    if not kind:
        return
    log(sid, n, kind, len(rules))
    out = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": rules}}
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))


main()
