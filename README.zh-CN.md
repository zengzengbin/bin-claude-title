# bin-claude-title

[English](README.md) | **简体中文**

让 **Claude Code 桌面端**的话题标题跟上你正在做的事情：自动命名为「类别 emoji + 对象｜目标」，话题再多也好找。

| 原来的标题 | 更容易找回的标题 |
| --- | --- |
| Codex 插件功能对标 | 🧩 bin-claude-title｜Claude 桌面版移植 |
| 回应中文问候 | 🧩 邮箱验证码｜过期排查 |

## 致谢

本项目是 [oil-oil/oil-codex-title](https://github.com/oil-oil/oil-codex-title) 的 **Claude Code 桌面端移植版**。
**衷心感谢原作者 [oil](https://github.com/oil-oil)**：命名规范（「emoji 对象｜目标」结构、类别体系、主线稳定与语言跟随规则）和整体设计思路均来自原项目，`hooks/naming_rules.md` 是对其 `prompts/naming.md` 的精简改写。原项目为 Codex 打造，基于 MIT 协议，本项目沿用 MIT 并保留原作者版权声明（见 [LICENSE](LICENSE)）。

## 工作方式（与原版的差异）

原版用 Stop hook 加独立的后台模型命名。Claude Code 桌面端没有公开的改名接口，且直接改磁盘上的会话文件不会被应用读取，因此本版改为：

1. `UserPromptSubmit` hook 在合适的轮次，把命名规则注入给当前对话的主 Agent；
2. 主 Agent 判断标题是否需要更新，需要时调用桌面端的 `set_session_title` 改名，不会向你提及。

触发时机：前 3 轮内标题还不是「emoji 对象｜目标」格式就注入（完整规则只注入一次，之后几轮只给一句提醒）；之后每 8 轮安排一次简短复核，等到轻量轮次（20 字以内的短消息，如「继续」）再注入，最多再等 3 轮。已合规的标题保持不变。注入内容要求主 Agent 先完成你的请求，最后再判断是否改名。

代价：会多消耗少量主模型 token，改名时多一次工具调用。没有独立模型、用量统计、闲置归档功能。

## 安装

要求：Windows 的 Claude 桌面应用（Code 标签）、Python 3。

```powershell
git clone https://github.com/zengzengbin/bin-claude-title
cd bin-claude-title
python install.py
```

安装脚本会把文件复制到 `~/.claude/hooks/bin-title/`，并在 `~/.claude/settings.json` 注册 hook（先备份为 `settings.json.pre-bin-title`，可重复运行）。新开会话即可生效。

## 控制

- 暂停：创建 `~/.claude/hooks/bin-title/paused` 文件；删除即恢复。
- 固定某个话题：创建 `~/.claude/hooks/bin-title/state/<会话ID>.pinned`。
- 注入日志：`~/.claude/hooks/bin-title/state/inject.log`，每次注入一行 JSON（时间、会话、轮次、类型 `full`/`retry`/`review`、字数）。超过 256 KB 时轮转为 `inject.log.1`（覆盖旧的那份），最多保留约 512 KB。闲置 30 天的会话计数会被清理。

## 已知限制

- 读取当前标题依赖 Windows 桌面端的数据目录（`%LOCALAPPDATA%\Claude-Data`），macOS / Linux 未适配。
- 只在桌面端验证过一个会话，属于预览版。

## 许可证

[MIT](LICENSE)，版权归原作者 oil 与本移植版作者共有。
