#!/usr/bin/env python3
"""Install oil-claude-title: copy hook files and register the UserPromptSubmit hook (idempotent)."""
import json, os, shutil, sys

home = os.path.expanduser("~/.claude")
dest = os.path.join(home, "hooks", "oil-title")
src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hooks")
os.makedirs(dest, exist_ok=True)
for name in ("title_hook.py", "naming_rules.md"):
    shutil.copy2(os.path.join(src, name), os.path.join(dest, name))

settings = os.path.join(home, "settings.json")
data = {}
if os.path.exists(settings):
    shutil.copy2(settings, settings + ".pre-oil-title")
    with open(settings, encoding="utf-8") as f:
        data = json.load(f)
cmd = '%s "%s"' % ("python" if os.name == "nt" else "python3", os.path.join(dest, "title_hook.py").replace("\\", "/"))
entries = data.setdefault("hooks", {}).setdefault("UserPromptSubmit", [])
if any(h.get("command") == cmd for e in entries for h in e.get("hooks", [])):
    print("hook already registered")
else:
    entries.append({"hooks": [{"type": "command", "command": cmd, "timeout": 10}]})
    with open(settings, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("hook registered:", cmd)
print("done. Start a new session to try it.")
