---
id: FIX-0015
uid: 649dbf
type: fix
status: open
stage: doing
title: 修复 monoco sync 幂等性缺陷导致 AGENTS.md 重复内容
created_at: '2026-02-04T21:32:48'
updated_at: '2026-02-04T21:39:31'
parent: EPIC-0030
dependencies: []
related:
- FEAT-0179
domains: []
tags:
- '#EPIC-0030'
- '#FEAT-0179'
- '#FIX-0015'
files:
- AGENTS.md
- monoco/core/injection.py
- tests/core/test_injector.py
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T21:32:48'
isolation:
  type: branch
  ref: FIX-0015-修复-monoco-sync-幂等性缺陷导致-agents-md-重复内容
  created_at: '2026-02-04T21:35:46'
---

## FIX-0015: 修复 monoco sync 幂等性缺陷导致 AGENTS.md 重复内容

## Objective

修复 `monoco sync` 命令的幂等性缺陷，该缺陷导致根目录 `AGENTS.md` 在 Managed Block 之外累积重复内容。当前 AGENTS.md 存在 4 次相同的 "Issue 管理" 章节重复（L290, L366, L442, L518），文件从预期的 ~300 行膨胀到 593 行。

## Problem Analysis

### 症状
```bash
$ grep -n "^# Issue 管理 (Agent 指引)" AGENTS.md
290:# Issue 管理 (Agent 指引)
366:# Issue 管理 (Agent 指引)
442:# Issue 管理 (Agent 指引)
518:# Issue 管理 (Agent 指引)

$ grep -n "MONOCO_GENERATED" AGENTS.md
3:<!-- MONOCO_GENERATED_START -->
288:<!-- MONOCO_GENERATED_END -->
```

所有重复内容都在 `<!-- MONOCO_GENERATED_END -->` (L288) 之后，不在 Managed Block 范围内。

### 根因

**PromptInjector 的设计缺陷**（`monoco/core/injection.py`）:

1. **边界检测策略**:
   - `_merge_content()` 优先检测 `<!-- MONOCO_GENERATED_END -->` 标记
   - 回退到检测同级或更高级别的 Markdown 标题
   - **问题**: 两种策略都只管理 Managed Block 内部，对外部内容无感知

2. **手动内容污染**:
   - 用户在 `<!-- MONOCO_GENERATED_END -->` 之后手动添加内容
   - 这些内容不在 Managed Block 范围内，`PromptInjector` 不会清理

3. **累积效应**:
   - 每次 `monoco sync` 正确替换 L3-L288 的 Managed Block
   - 但保留 L290-593 的手动内容
   - 多次手动复制粘贴 + 多次 sync 执行 → 重复累积

### 设计问题

**当前行为**: `PromptInjector` 是"追加器"而非"管理器"
- ✅ 正确管理 Managed Block 内部
- ❌ 不警告/清理 Managed Block 外部的手动内容
- ❌ 无法保证整个文件的幂等性

## Acceptance Criteria

- [x] **清理现有重复**: 删除 AGENTS.md 中 L290-593 的重复内容
- [x] **幂等性保证**: 多次执行 `monoco sync` 不会改变文件内容（如果 prompts 未变）
- [x] **警告机制**: 检测到 Managed Block 外部有手动内容时，输出警告信息
- [x] **文档更新**: 在 AGENTS.md 顶部添加注释，说明不应在 Managed Block 外部手动编辑
- [x] **测试验证**: 添加单元测试确保幂等性

## Technical Tasks

### Phase 1: 紧急清理（立即执行）
- [x] 手动删除 AGENTS.md 的 L290-593 重复内容
- [x] 提交清理结果

### Phase 2: 幂等性修复（核心修复）
- [x] **增强 PromptInjector**:
  - [x] 在 `inject()` 方法中添加外部内容检测逻辑
  - [x] 如果检测到 `<!-- MONOCO_GENERATED_END -->` 之后有非空内容:
    - [x] 输出警告: `⚠️ Warning: Manual content detected after Managed Block in {file}. Consider moving to a separate file.`

- [x] **添加文件头注释**:
  ```markdown
  <!--
  ⚠️ IMPORTANT: This file is partially managed by Monoco.
  - Content between MONOCO_GENERATED_START and MONOCO_GENERATED_END is auto-generated.
  - Do NOT manually edit the managed block.
  - Do NOT add content after MONOCO_GENERATED_END (use separate files instead).
  -->
  ```

### Phase 3: 测试与验证
- [x] **单元测试** (`tests/core/test_injection.py`):
  - [x] 测试幂等性: 连续两次 `inject()` 应产生相同结果
  - [x] 测试外部内容检测: 验证警告信息正确输出
  - [x] 测试边界情况: 空文件、仅 Managed Block、混合内容

- [ ] **集成测试**:
  - [ ] 在测试项目中执行 `monoco sync` 3 次
  - [ ] 验证 AGENTS.md 内容完全一致
  - [ ] 验证无重复内容生成

### Phase 4: 文档与发布
- [ ] 更新 `docs/` 中关于 AGENTS.md 管理的说明
- [ ] 在 CHANGELOG 中记录此修复

## Review Comments
