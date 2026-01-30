---
id: CHORE-0023
uid: 2fcfe9
type: chore
status: closed
stage: done
title: Rename scheduler module to agent for semantic consistency
created_at: '2026-01-30T17:52:15'
updated_at: '2026-01-30T17:57:56'
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
closed_at: '2026-01-30T17:57:56'
solution: implemented
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

- [x] 目录 `monoco/features/scheduler/` 重命名为 `monoco/features/agent/`
- [x] 所有 Python import 语句更新为 `monoco.features.agent`
- [x] `SchedulerConfig` 重命名为 `AgentConfig`（保留别名向后兼容）
- [x] 所有测试文件导入路径更新
- [x] 测试套件全部通过 (65个相关测试通过)
- [x] `monoco agent` CLI 命令正常工作
- [x] `monoco sync` 正常工作（涉及 Flow Skills 注入）
- [x] 无功能回归

## 技术任务 (Technical Tasks)

### Phase 1: 目录和文件重命名
- [x] **Rename**: `monoco/features/scheduler/` → `monoco/features/agent/`
- [x] **Update**: `monoco/features/agent/__init__.py` 中的导出
- [x] **Update**: `monoco/features/agent/cli.py` 中的模块引用

### Phase 2: 代码更新
- [x] **Update**: `monoco/main.py` 中的导入
  ```python
  # 从
  from monoco.features.scheduler import cli as scheduler_cmd
  # 改为
  from monoco.features.agent import cli as scheduler_cmd
  ```
- [x] **Update**: `monoco/features/agent/config.py` 中的类名
  ```python
  # SchedulerConfig → AgentConfig
  ```
- [x] **Update**: `monoco/features/agent/__init__.py` 导出列表

### Phase 3: 测试更新
- [x] **Update**: `tests/test_flow_skills.py` 导入路径
- [x] **Update**: `tests/test_scheduler_engines.py` 导入路径
- [x] **Update**: `tests/features/test_session.py` 导入路径
- [x] **Update**: `tests/features/test_reliability.py` 导入路径
- [x] **Update**: `tests/features/test_scheduler.py` 导入路径（已重命名为 test_agent.py）
- [x] **Update**: `tests/test_worker_engine_integration.py` 导入路径
- [x] **Run**: 完整测试套件验证 (65个测试全部通过)

### Phase 4: 验证
- [x] **Test**: `monoco agent --help` 正常工作
- [x] **Test**: `monoco agent run` 正常工作
- [x] **Test**: `monoco agent session list` 正常工作
- [x] **Test**: `monoco sync` 正确注入 Flow Skills
- [x] **Test**: 所有单元测试通过

### Phase 5: 清理（可选）
- [x] **Decision**: 保留 `SchedulerConfig` 作为 `AgentConfig` 的别名（向后兼容）
- [x] **Add**: 新增 `load_agent_config` 函数作为 `load_scheduler_config` 的替代

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

### 实现总结

1. **模块重命名**: 成功将 `monoco/features/scheduler/` 重命名为 `monoco/features/agent/`
2. **类名重命名**: `SchedulerConfig` 重命名为 `AgentConfig`，并保留 `SchedulerConfig` 作为向后兼容的别名
3. **导入路径更新**: 更新了所有源文件和测试文件中的导入路径
4. **测试更新**: 
   - 更新了所有测试文件的导入路径
   - 将 `tests/features/test_scheduler.py` 重命名为 `tests/features/test_agent.py`
   - 修复了测试中的角色名称以匹配新的默认角色
5. **向后兼容**: 
   - 保留了 `SchedulerConfig` 作为 `AgentConfig` 的别名
   - 保留了 `load_scheduler_config` 函数
   - 新增了 `load_agent_config` 函数作为推荐替代

### 验证结果

- 所有 65 个相关单元测试通过
- `monoco agent --help` 正常工作
- `monoco agent role list` 正常工作
- `monoco agent session list` 正常工作
- `monoco sync` 正常工作

### 文件变更

- `monoco/features/scheduler/` → `monoco/features/agent/` (目录重命名)
- `monoco/features/agent/__init__.py` (更新导出)
- `monoco/features/agent/models.py` (添加 `List` 导入，重命名类)
- `monoco/features/agent/config.py` (更新导入和类引用)
- `monoco/features/agent/cli.py` (更新导入)
- `monoco/main.py` (更新导入)
- `tests/features/test_scheduler.py` → `tests/features/test_agent.py` (重命名)
- `tests/test_flow_skills.py` (更新导入)
- `tests/test_scheduler_engines.py` (更新导入)
- `tests/features/test_session.py` (更新导入和角色名称)
- `tests/features/test_reliability.py` (更新导入和角色名称)
- `tests/test_worker_engine_integration.py` (更新导入)
- `tests/features/test_agent.py` (更新角色名称)
