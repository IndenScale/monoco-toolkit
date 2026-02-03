---
id: FEAT-0163
uid: ee3e62
type: feature
status: open
stage: review
title: 在 issue submit 运行过程中自动执行 sync-files
created_at: '2026-02-03T11:13:37'
updated_at: '2026-02-03T11:17:03'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0163'
files:
- '"Issues/Chores/closed/CHORE-0035-\346\266\210\351\231\244-asyncio-iscoroutinefunction-\345\274\203\347\224\250\350\255\246\345\221\212.md"'
- '"Issues/Chores/open/CHORE-0035-\346\266\210\351\231\244-asyncio-iscoroutinefunction-\345\274\203\347\224\250\350\255\246\345\221\212.md"'
- '"Issues/Features/open/FEAT-0163-\345\234\250-issue-submit-\350\277\220\350\241\214\350\277\207\347\250\213\344\270\255\350\207\252\345\212\250\346\211\247\350\241\214-sync-files.md"'
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- monoco/features/issue/commands.py
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T11:13:37'
isolation:
  type: branch
  ref: feat/feat-0163-在-issue-submit-运行过程中自动执行-sync-files
  created_at: '2026-02-03T11:13:39'
---

## FEAT-0163: 在 issue submit 运行过程中自动执行 sync-files

## Objective
在执行 `monoco issue submit` 时自动运行 `sync-files` 逻辑，以确保交付物的文件清单始终是最新的，防止后续原子合并因清单缺失或陈旧而失败。同时保留独立的 `monoco issue sync-files` 命令供手动使用。

## Acceptance Criteria
- [x] 执行 `monoco issue submit` 时，自动计算当前分支与 Trunk 的文件差异并更新 Ticket。
- [x] 即使开发者忘记手动运行 `sync-files`，在提交评审时 Ticket 的 `files` 字段也应是正确的。
- [x] 原有的独立 `monoco issue sync-files` 命令功能保持不变。

## Technical Tasks
- [x] 调研 `monoco/features/issue/commands.py` 中 `submit` 命令的实现。
- [x] 在 `submit` 函数逻辑中插入对 `core.sync_issue_files` 或相应逻辑的调用。
- [x] 添加回归测试或手动验证。

## Review Comments

### 实现总结 (2026-02-03)

1. **代码变更**: 在 `monoco/features/issue/commands.py` 中:
   - 添加了 `logging` 模块导入
   - 添加了 `logger = logging.getLogger(__name__)` 定义
   - 在 `submit` 命令中（第 395-400 行）嵌入了自动 `sync-files` 逻辑

2. **实现细节**:
   ```python
   # FEAT-0163: Automatically sync files before submission to ensure manifest completeness
   try:
        core.sync_issue_files(issues_root, issue_id, project_root)
   except Exception as se:
        # Just log warning, don't fail submit if sync fails (defensive)
        logger.warning(f"Auto-sync failed during submit for {issue_id}: {se}")
   ```
   - 自动 sync 在分支验证之后、stage 更新之前执行
   - 使用 try-except 包裹，确保 sync 失败不会阻塞 submit 流程（防御性设计）

3. **测试验证**:
   - 所有 146 个 issue 相关测试通过
   - 手动验证 `monoco issue sync-files` 独立命令功能正常
   - 代码导入测试通过

4. **设计决策**:
   - 保持独立 `sync-files` 命令可用性，供手动使用
   - 自动 sync 作为 submit 的前置步骤，无需用户干预
   - 错误处理采用警告而非抛出，避免影响现有工作流
