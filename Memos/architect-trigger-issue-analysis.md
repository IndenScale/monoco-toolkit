# Architect 触发机制问题分析

## 问题描述

Architect 被重复触发，尝试创建已经在 Memo inbox 中被修复/处理过的 Issue。

## 当前状态

- **Memo Inbox 中的 Pending 数量**: 7 条
- **默认阈值**: 5 条 (见 `MemoThresholdHandler.DEFAULT_THRESHOLD`)
- **当前状态**: 已超过阈值

## 架构分析

### 1. 双层状态管理机制

系统存在**两层独立的状态管理**:

#### Layer 1: MemoWatcher (文件系统监听层)

- **位置**: `monoco/core/watcher/memo.py`
- **职责**: 监听 `Memos/inbox.md` 文件变化
- **状态变量**:
  - `_last_pending_count`: 上次检测到的 pending memo 数量
  - `_threshold_crossed`: 是否已跨越阈值的标志位
- **触发逻辑**:
  ```python
  # Line 126-139
  if threshold_crossed and not self._threshold_crossed:
      # 仅在"首次跨越阈值"时触发
      event = MemoFileEvent(...)
      await self.emit(event)
  ```
- **重置机制**: `_threshold_crossed` 标志位在阈值下降时重置 (Line 156)

#### Layer 2: MemoThresholdHandler (业务逻辑层)

- **位置**: `monoco/core/automation/handlers.py`
- **职责**: 处理 MEMO_THRESHOLD 事件，调度 Architect Agent
- **状态变量**:
  - `_last_processed_count`: 上次处理的 memo 数量
- **触发逻辑**:

  ```python
  # Line 399-406
  if pending_count < self.threshold:
      return False

  if pending_count <= self._last_processed_count:
      # 已处理过相同或更少数量的 memo
      return False
  ```

- **问题**: `_last_processed_count` 仅在 `_handle()` 执行时更新 (Line 424)

### 2. 核心问题: 状态持久化缺失

#### 问题 1: 进程重启导致状态丢失

**场景**:

1. Daemon 启动时，`MemoWatcher._last_pending_count = 0`
2. 读取 `inbox.md`，发现 7 条 pending memos
3. `7 != 0` → 触发 `_handle_count_change(7)`
4. `7 >= 5 and not _threshold_crossed` → 发送 MEMO_THRESHOLD 事件
5. `MemoThresholdHandler` 收到事件，`7 > 0` (初始值) → 调度 Architect

**根本原因**:

- Watcher 和 Handler 的状态都是**内存状态**，进程重启后归零
- 无法区分"首次跨越阈值"和"重启后重新检测到已跨越阈值"

#### 问题 2: Architect 处理后未更新 Memo 状态

**场景**:

1. Architect 被调度，分析 7 条 memos
2. Architect 创建了对应的 Issues
3. **但**: Architect 没有修改 `inbox.md` 中的 memo 状态 (仍然是 `[ ] Pending`)
4. 下次 Daemon 重启或文件变化时，再次触发

**根本原因**:

- Architect 的 Prompt (Line 489-502) 中提到 "Organize or clear processed memos"
- 但这是**建议性**的，不是强制的
- 没有验证机制确保 Architect 完成了清理

#### 问题 3: 状态更新时机错误

**Handler 的 `_last_processed_count` 更新逻辑**:

```python
# Line 424
self._last_processed_count = pending_count
```

**问题**:

- 在 `_handle()` **开始时**就更新，而不是在 Architect **完成任务后**
- 如果 Architect 调度失败或任务未完成，状态已被错误更新
- 没有反馈机制确认 Architect 是否成功处理了 memos

### 3. 设计缺陷: "Emergent Workflow" 的副作用

根据 `handlers.py` 的架构注释 (Line 10-11):

> Architecture: No Workflow class or orchestration. Workflow emerges from
> the natural interaction of independent handlers.

**理念**: 去中心化、无状态的事件驱动架构

**副作用**:

1. **无闭环验证**: 没有机制确认 Architect 是否完成了任务
2. **无状态持久化**: 依赖内存状态，重启即丢失
3. **无幂等性保证**: 同一事件可能被重复处理

## 解决方案

### 方案 A: 引入状态持久化 (推荐)

**实现**:

1. 在 `.monoco/state/` 目录下保存 Watcher 和 Handler 的状态
2. 启动时加载上次的状态
3. 使用文件锁避免并发问题

**优点**:

- 彻底解决重启问题
- 符合 "Filesystem as API" 哲学
- 可审计、可调试

**缺点**:

- 增加文件 I/O
- 需要处理状态文件损坏的情况

### 方案 B: 强制 Architect 更新 Memo 状态

**实现**:

1. 修改 Architect Prompt，明确要求更新 memo 状态为 `[x]` 或删除
2. 在 Handler 中验证 `inbox.md` 的变化
3. 仅当 pending_count 下降时才更新 `_last_processed_count`

**优点**:

- 利用现有的文件系统状态
- 不引入新的状态存储

**缺点**:

- 依赖 Architect 的正确执行
- 如果 Architect 失败，会陷入死循环

### 方案 C: 引入去重机制

**实现**:

1. 为每个 memo 生成唯一 ID (基于内容哈希)
2. Handler 维护已处理的 memo ID 集合
3. 仅处理未见过的 memo

**优点**:

- 精确的去重
- 不依赖 Architect 的行为

**缺点**:

- 需要修改 memo 格式
- ID 集合需要持久化

### 方案 D: 冷却期机制 (临时缓解)

**实现**:

1. Handler 记录上次触发时间
2. 在一定时间内 (如 1 小时) 不重复触发
3. 使用指数退避策略

**优点**:

- 实现简单
- 立即缓解问题

**缺点**:

- 治标不治本
- 可能延迟合理的触发

## 推荐方案: A + B 组合

1. **短期**: 实现方案 D (冷却期) 立即缓解问题
2. **中期**: 实现方案 B (强制更新 Memo 状态)
3. **长期**: 实现方案 A (状态持久化) 作为基础设施

## 相关代码位置

- Watcher: `monoco/core/watcher/memo.py:69-201`
- Handler: `monoco/core/automation/handlers.py:356-503`
- Scheduler: `monoco/daemon/scheduler.py:113-136`
- Tests: `tests/core/watcher/test_memo_watcher.py`

## 测试建议

1. 添加测试用例: "Daemon 重启后不重复触发"
2. 添加测试用例: "Architect 处理后 memo 状态正确更新"
3. 添加集成测试: "完整的 Memo → Architect → Issue 流程"

## 附加发现

当前 `inbox.md` 中有 7 条 pending memos:

- [844f87] Post-Mortem (已有 Issue?)
- [325b48] UX Feedback (solution 字段问题)
- [0c262b] DevEx (Template 和 CLI 缺陷)
- [68eb0d] i18n (语言检测阈值优化)
- [e691f9] Arch Decision (Artifacts 架构复盘)
- [b3143c] workflow (issue close 分支问题)
- [673948] architecture (IM 协作模式讨论)

这些 memo 中有些可能已经有对应的 Issue，需要人工确认。
