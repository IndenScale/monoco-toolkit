---
id: FIX-0022
type: fix
status: closed
stage: done
title: Add i18n source language validation for Memo module
created_at: '2026-01-30T15:13:57'
updated_at: '2026-01-30T15:17:08'
priority: normal
parent: EPIC-0000
dependencies: []
related: []
domains:
- Guardrail
tags:
- '#FIX-0022'
- '#EPIC-0000'
files:
- monoco/features/memo/cli.py
- monoco/features/memo/core.py
- tests/features/memo/test_memo_i18n.py
criticality: high
closed_at: '2026-01-30T15:17:08'
solution: implemented
isolation:
  type: branch
  ref: feat/fix-0022-add-i18n-source-language-validation-for-memo-modul
  created_at: '2026-01-30T15:13:57'
author: IndenScale
created: '2026-01-30'
---

## FIX-0022: Add i18n source language validation for Memo module

**问题**:
目前 `monoco memo` 模块缺乏对输入内容的语言检查。即使 `workspace.yaml` 中配置了 `i18n.source_lang` 为 `zh`，系统仍允许用户（或 Agent）提交英文内容，导致数据一致性被破坏。

**原因**:
`monoco/features/memo/core.py` 中的 `add_memo` 函数直接接收字符串并写入文件，没有任何校验逻辑。

**修复方案**:
在 `monoco memo add` 命令执行路径中引入语言检测机制。

1.  **配置读取**: 从 `monoco.core.config` 获取 `i18n.source_lang` 设置。
2.  **语言检测**: 使用轻量级 NLP 库（如 `langdetect` 或简单的字符集启发式算法）检测输入内容的语言。
3.  **强制/警告**:
    - 如果检测到的语言与 `source_lang` 不匹配，阻止提交并报错（Error）。
    - 提供 `--force` 参数允许绕过检查（Escape Hatch）。

**Acceptance Criteria**:
- [x] 当 `source_lang: zh` 时，`monoco memo add "Hello world"` 应失败并提示语言不匹配。
- [x] `monoco memo add "你好世界"` 应成功。
- [x] `monoco memo add "Hello world" --force` 应成功。
- [x] 实现不应引入过重的依赖（如大型 ML 模型）。

## Technical Tasks:
- [x] 调研 Python 轻量级语言检测方案。
- [x] 在 `monoco/features/memo/cli.py` 或 `core.py` 中实现检测逻辑。
- [x] 添加 `--force` 选项支持。
- [x] 编写测试用例验证拦截和绕过逻辑。

## Review Comments
- 2026-01-30:
  - 采用了轻量级的 Unicode 字符范围检测方法，符合 KISS 原则，避免了引入大型 NLP 依赖。
  - 在 CLI 层实现了校验逻辑，并通过 `--force` 提供了逃生舱。
  - 已添加充足的单元测试覆盖中/英、强制通过等场景。