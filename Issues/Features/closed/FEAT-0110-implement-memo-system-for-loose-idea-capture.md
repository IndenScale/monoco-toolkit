---
id: FEAT-0110
uid: ce5d27
type: feature
status: closed
stage: done
title: Implement Memo System for loose idea capture
created_at: '2026-01-29T17:08:49'
updated_at: 2026-01-29 17:13:15
parent: EPIC-0001
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0001'
- '#FEAT-0110'
files: []
opened_at: '2026-01-29T17:08:49'
closed_at: '2026-01-29T17:13:05'
solution: implemented
---

## FEAT-0110: Implement Memo System for loose idea capture

## 目标
提供一个低摩擦的 CLI 机制，将转瞬即逝的想法（Memos）捕捉到简单的 Markdown 收件箱（`Memos/inbox.md`）中，无需创建结构化 issue 的开销。

## 验收标准
- [x] CLI `monoco memo add <content>` 将新备忘录追加到 `Memos/inbox.md`。
- [x] CLI `monoco memo list` 显示最近的备忘录。
- [x] 数据持久化使用简单的 Markdown 仅追加结构。

## 技术任务

- [x] 实现 `monoco/features/memo` 包结构。
- [x] 实现 `core.py`：使用正则解析的添加/列表逻辑。
- [x] 实现 `cli.py`：`add` 和 `list` 的 Typer 命令。
- [x] 集成到 `monoco/main.py` CLI 注册表。
- [x] 验证上下文/配置解析逻辑正确处理 `issues_root`。

## 评审意见
- 手动测试了 `monoco memo add` 和 `monoco memo list`。
- 验证了 `Memos/inbox.md` 中的存储文件格式。

## Review Comments

- [x] Self-Review
