---
id: FIX-0008
uid: ff72a9
type: fix
status: closed
stage: done
title: '修复 monoco issue close 无法正确解析 isolation.ref 中的 branch: 前缀的问题'
created_at: '2026-02-03T09:52:32'
updated_at: 2026-02-03 09:52:48
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0008'
files: []
criticality: high
solution: implemented
opened_at: '2026-02-03T09:52:32'
isolation:
  type: branch
  ref: feat/fix-0008-修复-monoco-issue-close-无法正确解析-isolation-ref-中的-bran
  path: null
  created_at: '2026-02-03T09:52:48'
---

## FIX-0008: 修复 monoco issue close 无法正确解析 isolation.ref 中的 branch: 前缀的问题

## Objective
当 `monoco issue close` 处理 `isolation.ref` 时，如果前缀包含 `branch:` 或 `worktree:`，会导致 Git 无法找到物理分支而报错。本任务旨在修复该解析逻辑。

## Acceptance Criteria
- [x] `monoco issue close` 能够正确识别并剥离 `isolation.ref` 中的 `branch:` 前缀。
- [x] `FEAT-0160` 可以使用该指令正常关闭。

## Technical Tasks
- [x] 调研 `monoco issue close` 的核心逻辑（通常在 `monoco/features/issue/cli.py` 或相关 core 模块中）。
- [x] 修正 `isolation` 模型的解析或在 `close` 命令中进行预处理。
- [x] 验证修复效果。

## Review Comments

### 修复总结 (2026-02-03)

**问题**: `monoco issue close` 在处理 `isolation.ref` 时，如果 ref 包含 `branch:` 或 `worktree:` 前缀，会导致 Git 命令失败。

**解决方案**: 在 `monoco/features/issue/core.py` 中添加 `_parse_isolation_ref()` helper 函数，用于剥离前缀：

```python
def _parse_isolation_ref(ref: str) -> str:
    if not ref:
        return ref
    for prefix in ("branch:", "worktree:"):
        if ref.startswith(prefix):
            return ref[len(prefix):]
    return ref
```

**修改位置**:
1. `sync_issue_files()` - 第 1190 行
2. `merge_issue_changes()` - 第 1268 行  
3. `prune_issue_resources()` - 第 1106 行和第 1132 行

**验证**:
- 单元测试通过：133 个测试全部通过
- 手动验证 `_parse_isolation_ref` 函数正确处理各种前缀情况
