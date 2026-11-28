# bin-claude-title

**English** | [简体中文](README.zh-CN.md)

Keep your **Claude Code desktop** session titles in step with what you are actually doing. Sessions are auto-named as `category emoji + subject｜goal`, so they stay easy to find no matter how many you have.

| Before | After |
| --- | --- |
| Codex plugin comparison | 🧩 bin-claude-title｜Claude desktop port |
| Reply to greeting | 🧩 Email verification｜Fix expiry |

## Acknowledgements

This project is a **Claude Code desktop port** of [oil-oil/oil-codex-title](https://github.com/oil-oil/oil-codex-title).
**Heartfelt thanks to the original author, [oil](https://github.com/oil-oil)**: the naming convention (the `emoji subject｜goal` structure, the category system, the rules for keeping a stable main thread and following the user's language) and the overall design all come from the original project. `hooks/naming_rules.md` is a condensed rewrite of its `prompts/naming.md`. The original was built for Codex under the MIT license; this project stays MIT and keeps the original copyright notice (see [LICENSE](LICENSE)).

## How it works (and how it differs from the original)

The original uses a Stop hook plus a separate background model. Claude Code desktop has no public rename API, and editing the session file on disk is not picked up by the app, so this version works differently:

1. A `UserPromptSubmit` hook injects the naming rules into the current conversation's main agent at suitable turns.
2. The main agent decides whether the title needs updating and, if so, calls the desktop app's `set_session_title` silently.

When it fires: during the first 3 turns, while the title is not yet in `emoji subject｜goal` form (the full rules are injected once; later turns get a one-line reminder). After that, a short review falls due every 8th turn and waits for a light turn (a prompt of 20 characters or fewer, such as "continue"), forced after 3 more turns at most. A title that already complies is left alone. The injected text asks the agent to finish your request first and only then consider the title.

Trade-offs: a few extra main-model tokens per injection, plus one extra tool call when a rename happens. There is no separate model, usage ledger, or idle-session archiving.

## Install

Requirements: Claude desktop app on Windows (Code tab), Python 3.

```powershell
git clone https://github.com/zengzengbin/bin-claude-title
cd bin-claude-title
python install.py
```

The installer copies the files to `~/.claude/hooks/bin-title/` and registers the hook in `~/.claude/settings.json` (backed up first as `settings.json.pre-bin-title`; safe to re-run). Start a new session to try it.

## Controls

- Pause: create the file `~/.claude/hooks/bin-title/paused`; delete it to resume.
- Pin a session's title: create `~/.claude/hooks/bin-title/state/<session-id>.pinned`.
- Injection log: `~/.claude/hooks/bin-title/state/inject.log`, one JSON line per injection (time, session, turn, kind `full`/`retry`/`review`, characters). Past 256 KB it is rotated to `inject.log.1` (overwriting the older one), so at most about 512 KB is kept. Per-session counters idle for 30 days are pruned.

## Known limitations

- Reading the current title relies on the Windows desktop data directory (`%LOCALAPPDATA%\Claude-Data`); macOS and Linux are not supported yet.
- Verified on a single session in the desktop app only; treat it as a preview.

## License

[MIT](LICENSE). Copyright is shared by the original author oil and the author of this port.
