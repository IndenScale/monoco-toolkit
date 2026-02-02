---
id: CHORE-0033
uid: 4f5dca
type: chore
status: open
stage: review
title: 重构 monoco issue start：移除 --branch 选项并将其设为默认
created_at: '2026-02-02T21:19:17'
updated_at: '2026-02-02T22:21:38'
parent: EPIC-0000
dependencies: []
related: []
domains:
- Foundation
tags:
- '#CHORE-0033'
- '#EPIC-0000'
files:
- Issues/Chores/open/CHORE-0033-simplify-issue-start-by-removing-branch-flag-and-m.md
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-02T21:19:17'
isolation:
  type: branch
  ref: feat/chore-0033-重构-monoco-issue-start-移除-branch-选项并将其设为默认
  created_at: '2026-02-02T21:28:25'
---

## CHORE-0033: 重构 monoco issue start：移除 --branch 选项并将其设为默认

## Objective

### 核心背景
Monoco 的哲学是 **"Branch is the isolation unit"**。目前 `monoco issue start` 虽然默认开启了 branch 模式，但在文档和 Agent 惯例中仍强制要求显式输入 `--branch`。这种冗余不仅增加了操作负担，也导致协议逻辑显得不够整洁。

### 修改目标
1. **简化命令**：彻底移除 `start` 命令中的 `--branch` 选项。
2. **确定性行为**：默认即开启 Branch 模式，仅通过 `--direct` 或 `--worktree` 进行显式切换。
3. **协议同步**：确保所有 Agent 文档、角色提示词、技能描述与该变更保持全局一致，防止 Agent 产生无效输出。

## Acceptance Criteria
- [x] `monoco issue start` 彻底移除 `--branch/--no-branch` flag。
- [x] 默认执行行为保持为：从 TRUNK 创建并切换到 feature branch。
- [x] `GEMINI.md` 更新，删除“强制要求 --branch”的陈述。
- [x] 全局搜索并清理包含 `--branch` 参数的 Agent 提示词、Skills 和 Roles 内容。
- [x] 所有单元测试已适配该变更。

## Technical Tasks

### Phase 1: 系统性调研与影响评估
- [x] 全局搜索 `monoco issue start` 在项目中的所有引用位置
- [x] 识别所有依赖 `--branch` 的 Role 提示词和 Skill 指令
- [x] 检查 CI/CD 或 Hooks 中是否有涉及该 flag 的硬编码

### Phase 2: CLI 核心修改
- [x] 修改 `monoco/features/issue/commands.py`：
  - [x] 移除 `--branch` 参数定义
  - [x] 重构内部逻辑，确保 isolation 模式缺省为 `branch`
  - [x] 保留 `--direct` 作为特权模式开关
- [x] 验证 `monoco issue start --help` 的输出正确性

### Phase 3: 宪法与 Agent 协议更新
- [x] 更新 `GEMINI.md` (及所有 I18n 副本) 中的工作流章节
- [x] 更新 `.agent/workflows/` 下的指令模板
- [x] 更新核心 Role 的系统提示词内容（如果存在于代码库中）

### Phase 4: 验证与验收
- [x] 更新并运行 `tests/features/issue/` 相关的单元测试
- [x] 模拟 Agent 执行流程，确保其不再输出 `--branch`
- [x] 提交并闭环 Issue

## Review Comments

### 变更摘要

1. **CLI 核心修改** (`monoco/features/issue/commands.py`):
   - 移除了 `--branch/--no-branch` 参数定义
   - 重构内部逻辑：`branch = not (direct or worktree)`，默认即 branch 模式
   - 保留了 `--direct` 和 `--worktree` 作为显式切换选项
   - 更新了 docstring，删除了 `--no-branch` 的引用

2. **单元测试更新** (`tests/features/issue/test_cli_logic_start.py`):
   - `test_start_command_default_branch`: 保持原有测试，验证默认 branch 模式
   - `test_start_command_direct_mode`: 重命名并更新，测试 `--direct` 模式
   - `test_start_command_worktree_mode`: 新增测试，验证 `--worktree` 模式

3. **文档更新**:
   - `GEMINI.md`, `AGENTS.md`, `CLAUDE.md`, `QWEN.md`: 删除所有 `--branch` 强制要求
   - Agent 资源文件: 更新 skills 和 workflows，移除 `--branch` 参数

### 验证结果
- 所有单元测试通过
- `monoco issue start --help` 输出正确，不再显示 `--branch` 选项
- 全局搜索确认无残留的 `--branch` 参数引用（排除 `.references/` 只读目录）
