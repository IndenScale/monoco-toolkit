---
id: FEAT-0165
uid: a5a9ae
type: feature
status: open
stage: review
title: 重构 Memo Inbox 为信号队列模型：消费即销毁
created_at: '2026-02-03T14:24:54'
updated_at: '2026-02-04T10:03:49'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0165'
files:
- '"Issues/Features/open/FEAT-0165-\351\207\215\346\236\204-memo-inbox-\344\270\272\344\277\241\345\217\267\351\230\237\345\210\227\346\250\241\345\236\213-\346\266\210\350\264\271\345\215\263\351\224\200\346\257\201.md"'
- .monoco/project.yaml
- AGENTS.md
- monoco/core/automation/handlers.py
- monoco/core/watcher/memo.py
- monoco/features/memo/cli.py
- monoco/features/memo/core.py
- monoco/features/memo/models.py
- monoco/features/memo/resources/en/AGENTS.md
- monoco/features/memo/resources/zh/AGENTS.md
- tests/core/automation/test_memo_threshold_handler.py
- tests/core/watcher/test_memo_watcher.py
- tests/features/memo/test_memo_lifecycle.py
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T14:24:54'
isolation:
  type: branch
  ref: feat/feat-0165-重构-memo-inbox-为信号队列模型-消费即销毁
  created_at: '2026-02-04T09:54:17'
---

## FEAT-0165: 重构 Memo Inbox 为信号队列模型：消费即销毁

## Objective

### 问题陈述

当前 `monoco serve` 启动后出现混乱：
1. **重复创建 Issue**：已处理的 memo 在每次 serve 重启后都被重新处理
2. **状态管理失效**：Memo 的 `status` 字段（pending/tracked/resolved）依赖内存状态 `_last_processed_count`，重启后丢失
3. **流程断裂**：Architect 被期望"标记 memo 为已处理"，但缺乏强制执行机制

### 根本原因

设计范式的混淆：**试图让 Inbox 同时承担"处理队列"和"历史档案"两个矛盾角色**。

### 核心洞察

> Memo 是**信号**，不是**资产**。

- 信号的价值在于触发行动，而非被长期存储
- 信号被接收即完成使命
- 如果信号重要，它会再次出现
- 历史追溯应依赖 Git，而非应用层状态管理

### 新范式定义

| 维度 | 原设计 (CRUD+State) | 新设计 (Signal+Queue) |
|------|--------------------|----------------------|
| 本质 | Memo 是需要管理的记录 | Memo 是触发 Architect 的信号 |
| 生命周期 | pending → tracked → resolved/dismissed | 存在 → 消失 |
| 存储方式 | 单文件 inbox.md，更新 status 字段 | 文件存在性即状态 |
| 消费语义 | 读取并更新状态 | 读取并删除 |
| 历史追溯 | status 字段 + ref 关联 | Git 考古 |
| 幂等性 | 依赖内存状态 `_last_processed_count` | 天然幂等（已删除则无） |

## Acceptance Criteria

- [x] MemoWatcher 检测到 inbox.md 有内容时触发事件
- [x] MemoThresholdHandler 在调度 Architect 前**原子性清空** inbox.md
- [x] Architect Prompt 携带 memo 内容，不再读取文件
- [x] 删除 `Memo.status` 字段及其相关逻辑
- [x] 删除 `Memo.ref` 字段（Issue 通过 `source_memo` 追溯，非 memo 指向 issue）
- [x] 删除 `monoco memo link`、`monoco memo resolve` 命令
- [x] 更新 `monoco memo list` 只显示当前 inbox 内容（无 status 过滤）
- [x] 系统重启后不会重复处理已消费的 memo

## Technical Tasks

### Phase 1: 核心逻辑重构

- [x] 修改 `MemoThresholdHandler._handle()` 实现"读取即清空"语义
  - 在 `await self.scheduler.schedule(task)` 之前清空 inbox.md
  - 将解析后的 memos 列表嵌入 Prompt，而非让 Architect 读取文件
- [x] 修改 `MemoWatcher._count_pending_memos()` 为检测"文件非空"而非"统计数量"
- [x] 使用原子文件写操作，防止并发问题

### Phase 2: 模型简化

- [x] 删除 `Memo.status` 字段（Literal["pending", "tracked", "resolved", "dismissed"]
- [x] 删除 `Memo.ref` 字段
- [x] 简化 `Memo.to_markdown()`，移除 status 相关渲染
- [x] 更新 `parse_memo_block()`，移除 status 解析逻辑

### Phase 3: CLI 清理

- [x] 删除 `monoco memo link` 命令
- [x] 删除 `monoco memo resolve` 命令
- [x] 简化 `monoco memo list`，移除 `--status` 过滤参数
- [x] 更新 `monoco memo delete` 为物理删除（保持现有行为）

### Phase 4: 文档与测试

- [x] 更新 AGENTS.md 中关于 Memo 的描述
- [x] 更新 Architect Prompt 模板，说明新语义
- [x] 编写测试：模拟 serve 重启，验证 memo 不被重复处理
- [x] 编写测试：验证 inbox 清空后 Architect 仍能获得内容

## Design Principles

```
Filesystem as Queue
├── 文件存在 = 信号待处理
├── 文件删除 = 信号已消费
└── 空文件 = 无信号

Git as Archive
├── git log = 历史查询
├── git show <commit>:Memos/inbox.md = 找回已删除 memo
└── 应用层不负责历史管理

Atomic Consumption
├── Handler 负责清空，不依赖 Agent 自律
├── 调度前清空 = 即使 Architect 失败也不会重复
└── Prompt 携带数据 = 文件清空不影响处理
```

## Review Comments

### 实现总结

1. **MemoThresholdHandler** (`monoco/core/automation/handlers.py`):
   - 新增 `_load_and_clear_memos()` 方法，在调度前原子性加载并清空 inbox
   - 更新 `_build_prompt()` 将 memos 嵌入 prompt，而非让 Architect 读取文件
   - 移除 `_last_processed_count` 状态依赖

2. **MemoWatcher** (`monoco/core/watcher/memo.py`):
   - 从 `_count_pending_memos()` 改为 `_count_memos()`，基于 header 模式匹配
   - 简化统计逻辑，移除 checkbox 状态检查
   - 更新 stats 字段名从 `pending_count` 到 `memo_count`

3. **Memo 模型** (`monoco/features/memo/models.py`):
   - 删除 `status` 和 `ref` 字段
   - 更新 `to_markdown()` 移除 status 相关渲染

4. **Core 模块** (`monoco/features/memo/core.py`):
   - 更新 `parse_memo_block()` 移除 status/ref 解析
   - 删除 `update_memo()` 函数（不再需要状态更新）

5. **CLI** (`monoco/features/memo/cli.py`):
   - 删除 `link` 和 `resolve` 命令
   - 简化 `list` 命令，移除 `--status` 过滤
   - 更新提示信息说明 Signal Queue 语义

6. **文档**:
   - 更新根目录 `AGENTS.md` 和 feature 资源文件
   - 创建英文版 `AGENTS.md`

7. **测试**:
   - 更新 `test_memo_watcher.py` 匹配新实现
   - 新增 `test_memo_threshold_handler.py` 测试 Signal Queue 语义
   - 更新 `test_memo_lifecycle.py` 测试新模型

### 测试覆盖

- 32 个测试全部通过
- 包含关键测试：`test_restart_does_not_reprocess` 验证重启幂等性
