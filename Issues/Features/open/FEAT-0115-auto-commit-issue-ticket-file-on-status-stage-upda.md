---
id: FEAT-0115
uid: ccebca
type: feature
status: open
stage: draft
title: Auto-commit issue ticket file on status/stage updates
created_at: '2026-01-30T08:54:01'
updated_at: '2026-01-30T08:54:01'
parent: EPIC-0001
dependencies: []
related:
- FIX-0020
domains: []
tags:
- '#EPIC-0001'
- '#FEAT-0115'
- '#FIX-0020'
files: []
opened_at: '2026-01-30T08:54:01'
---

## FEAT-0115: Auto-commit issue ticket file on status/stage updates

## Objective
当通过 `monoco issue` CLI 修改 Issue 的状态（status）或阶段（stage）时，系统应自动执行 `git add` 和 `git commit` 操作，仅针对受影响的 Issue Markdown 文件。

这旨在解决“任务流转”与“版本记录”脱节的问题，确保任务状态的物理移动能够实时且原子地持久化到 Git 历史中。

## Acceptance Criteria
- [ ] 当执行 `open`, `close`, `backlog`, `start`, `submit` 等改变 Issue 文件内容的命令时，自动 `git add` 该文件。
- [ ] 自动生成原子化的 Commit Message，例如 `chore(issue): close FIX-0020` 或 `chore(issue): start FEAT-0115`。
- [ ] **范围限制**：严禁自动 commit 业务代码或非当前 Issue 的文件。
- [ ] **环境感知**：若当前目录不在 Git 仓库内，平滑降级（不报错，仅提示）。
- [ ] **可配置性**：提供 `--no-commit` 全局参数或配置项以禁用此自动行为。

## Technical Tasks

### 1. 核心链路实现
- [ ] 在 `monoco.features.issue.core.update_issue` 或对应的 CLI 处理层中，增加对 Git 仓库的检测逻辑。
- [ ] 封装 `IssueGitService` 用于处理针对特定文件的原子 Commit 操作。
- [ ] 确保在 `close` 引发的物理移动（rename/unlink）后，Git 正确追踪到删除旧文件并添加新文件的动作。

### 2. 参数支持
- [ ] 为相关 CLI 命令增加 `--no-commit` flag。

### 3. 测试验证
- [ ] 编写模拟 Git 环境的测试用例，验证该功能不会触碰“脏”的工作区（Dirty Workspace）中的其他业务文件。
- [ ] 验证 Commit Message 模板符合规范。

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
