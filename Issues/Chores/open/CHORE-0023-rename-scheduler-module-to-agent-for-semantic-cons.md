---
id: CHORE-0023
uid: 2fcfe9
type: chore
status: open
stage: doing
title: Rename scheduler module to agent for semantic consistency
created_at: '2026-01-30T17:52:15'
updated_at: '2026-01-30T17:57:20'
parent: EPIC-0022
dependencies: []
related:
- FEAT-0122
- FEAT-0123
domains:
- AgentOnboarding
tags:
- '#CHORE-0023'
- '#EPIC-0022'
files: []
criticality: low
opened_at: '2026-01-30T17:52:15'
isolation:
  type: branch
  ref: feat/chore-0023-rename-scheduler-module-to-agent-for-semantic-cons
  created_at: '2026-01-30T17:55:48'
---

## CHORE-0023: Rename scheduler module to agent for semantic consistency

## 目标 (Objective)

将 `monoco/features/scheduler` 模块重命名为 `monoco/features/agent`，以消除命名与职责的不一致。

**背景**:
- CLI 命令是 `monoco agent`，但模块名是 `scheduler`
- 模块实际职责是 Agent 生命周期管理（Session、Role、Worker），而非任务调度
- 命名不一致增加了用户和开发者的认知负担

**价值**:
- 提升代码可读性和可维护性
- 与 CLI 命令保持一致
- 为 Agent 功能扩展奠定清晰的命名基础

## 核心变更范围 (Scope)

### 1. 模块目录重命名
```
monoco/features/scheduler/ → monoco/features/agent/
```

### 2. 类名重命名（可选但推荐）
| 当前类名 | 新类名 | 理由 |
|---------|--------|------|
| `SchedulerConfig` | `AgentConfig` | 配置的是 Agent 角色，非调度器 |
| `SessionManager` | 保持不变 | 已准确描述职责 |
| `RoleTemplate` | 保持不变 | 已准确描述职责 |

### 3. 导入路径更新
所有引用 `monoco.features.scheduler` 的文件需要更新。

## 验收标准 (Acceptance Criteria)

- [ ] 目录 `monoco/features/scheduler/` 重命名为 `monoco/features/agent/`
- [ ] 所有 Python import 语句更新为 `monoco.features.agent`
- [ ] `SchedulerConfig` 重命名为 `AgentConfig`（或保留别名）
- [ ] 所有测试文件导入路径更新
- [ ] 测试套件全部通过
- [ ] `monoco agent` CLI 命令正常工作
- [ ] `monoco sync` 正常工作（涉及 Flow Skills 注入）
- [ ] 无功能回归

## 技术任务 (Technical Tasks)

### Phase 1: 目录和文件重命名
- [ ] **Rename**: `monoco/features/scheduler/` → `monoco/features/agent/`
- [ ] **Update**: `monoco/features/agent/__init__.py` 中的导出
- [ ] **Update**: `monoco/features/agent/cli.py` 中的模块引用

### Phase 2: 代码更新
- [ ] **Update**: `monoco/main.py` 中的导入
  ```python
  # 从
  from monoco.features.scheduler import cli as scheduler_cmd
  # 改为
  from monoco.features.agent import cli as agent_cmd
  ```
- [ ] **Update**: `monoco/core/skills.py` 中的 Flow Skills 路径引用
- [ ] **Update**: `monoco/features/agent/config.py` 中的类名
  ```python
  # SchedulerConfig → AgentConfig
  ```
- [ ] **Update**: `monoco/features/agent/__init__.py` 导出列表

### Phase 3: 测试更新
- [ ] **Update**: `tests/test_flow_skills.py` 导入路径
- [ ] **Update**: `tests/test_scheduler_engines.py` 导入路径
- [ ] **Update**: `tests/features/test_session.py` 导入路径
- [ ] **Update**: `tests/features/test_reliability.py` 导入路径
- [ ] **Update**: `tests/features/test_scheduler.py` 导入路径（考虑重命名为 test_agent.py）
- [ ] **Update**: `tests/test_worker_engine_integration.py` 导入路径
- [ ] **Run**: 完整测试套件验证

### Phase 4: 验证
- [ ] **Test**: `monoco agent --help` 正常工作
- [ ] **Test**: `monoco agent run` 正常工作
- [ ] **Test**: `monoco agent session list` 正常工作
- [ ] **Test**: `monoco sync` 正确注入 Flow Skills
- [ ] **Test**: 所有单元测试通过

### Phase 5: 清理（可选）
- [ ] **Decision**: 是否保留 `SchedulerConfig` 作为 `AgentConfig` 的别名（向后兼容）
- [ ] **Remove**: 如不需要，删除兼容性别名

## 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 遗漏的 import 引用 | 中 | 高 | 使用 IDE 全局搜索 + 运行时测试 |
| 测试覆盖率不足 | 低 | 中 | 运行完整测试套件 |
| 外部引用（如文档） | 低 | 低 | 搜索并更新文档中的代码示例 |

## 相关资源

- 影响文件统计:
  - `monoco/features/scheduler/*` → 11 个文件
  - `tests/` 中的测试文件 → 5+ 个文件
  - `monoco/main.py` → 1 处 import
  - `monoco/core/skills.py` → 可能的路径引用

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
