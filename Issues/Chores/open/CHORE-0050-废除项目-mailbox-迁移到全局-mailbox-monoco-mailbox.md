---
id: CHORE-0050
uid: c9153b
type: chore
status: open
stage: done
title: 废除项目 mailbox，迁移到全局 mailbox (~/.monoco/mailbox)
created_at: '2026-02-10T12:23:01'
updated_at: '2026-02-10T12:23:01'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0050'
- '#EPIC-0000'
files:
- src/monoco/features/connector/protocol/constants.py
- src/monoco/features/mailbox/commands.py
- src/monoco/features/courier/daemon.py
criticality: low
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-10T12:23:01'
---

## CHORE-0050: 废除项目 mailbox，迁移到全局 mailbox (~/.monoco/mailbox)

## Objective
废除项目级别的 mailbox (`<project>/.monoco/mailbox/`)，统一使用全局 mailbox (`~/.monoco/mailbox/`)。

**背景**: 当前每个项目维护自己的 mailbox，导致：
1. 消息分散在各项目中，难以统一管理
2. Courier 需要知道项目路径才能处理消息
3. 跨项目消息路由复杂

**目标**: 将 mailbox 提升到全局级别，所有项目共享同一个 mailbox，通过消息元数据中的 `project` 字段来标识消息归属。

## Acceptance Criteria
- [x] 所有消息存储在 `~/.monoco/mailbox/` 下，而非项目目录
- [x] `monoco mailbox` 命令使用全局 mailbox
- [x] Courier daemon 使用全局 mailbox
- [x] 入站消息包含 `project` 字段标识目标项目
- [x] 出站消息包含 `project` 字段标识来源项目
- [x] 现有项目级 mailbox 路径不再被创建或使用
- [x] ADR-003 文档已更新反映新架构

## Technical Tasks

- [x] 修改 `constants.py`: 更新 `DEFAULT_MAILBOX_ROOT` 指向全局路径
- [x] 修改 `mailbox/commands.py`: 更新 `_get_mailbox_root()` 返回全局路径
- [x] 修改 `mailbox/store.py`: 移除对项目路径的依赖（如需要）
- [x] 修改 `courier/daemon.py`: 更新 `mailbox_root` 初始化
- [x] 修改 `courier/state.py`: 更新 `MessageStateManager` 路径处理
- [x] 更新 `ADR-003-Mailbox-Protocol-Schema.md`: 更新路径说明
- [x] 运行 `monoco issue lint` 验证 Issue 格式

## Implementation Details

### 路径变更
```python
# Before (项目级)
DEFAULT_MAILBOX_ROOT = Path(".monoco") / "mailbox"  # -> <project>/.monoco/mailbox

# After (全局)
DEFAULT_MAILBOX_ROOT = Path.home() / ".monoco" / "mailbox"  # -> ~/.monoco/mailbox
```

### 消息 Schema 变更
入站/出站消息需要包含 `project` 字段：
```yaml
---
id: msg_xxx
provider: dingtalk
project: my-project  # 新增：标识消息归属项目
# ...
---
```

### 影响范围
- `monoco mailbox list/read/send/claim/done/fail` 命令
- Courier daemon 启动和运行
- DingTalk Stream adapter 消息写入
- Outbound message processor

## Breaking Changes
- 现有项目级 mailbox 中的消息需要手动迁移或归档
- 配置文件中不再支持项目级 mailbox 路径自定义

## Review Comments
