# 静态分析与不变量 (Lint & Invariants)

在 Monoco 中，Issue 不仅仅是文本，它是**代码**。因此，它必须像代码一样经过编译（Lint）和测试（Verify）。

## 1. Issue Linter

`monoco issue lint` 是 Monoco 的“编译器”。它基于 Pydantic Schema 对 Issue 文件进行严格的静态分析。

### 1.1 基础完整性检查
- **Schema Validation**: 检查 YAML Front Matter 是否符合规范（字段类型、必填项）。
- **Link Integrity (引用治理)**: 检查 `parent` 指向的 Epic 是否真实存在，防止引用破碎。
- **Placeholder Cleanup (占位符治理)**: 扫描 Body 文本，检查是否残留 `TBD`, `TODO`, `[待补充]` 等占位符。在进入 `review` 阶段前，必须清除所有占位文本。
- **File Existence**: 检查 `files` 列表中的文件路径是否有效。

### 1.2 动态鲜活性校验 (Vitality Check)
Linter 不仅检查文本，还检查文本与代码库的**一致性**：
- **Stale File Check**: 检查 `files` 列表中的文件是否真的在当前分支被修改过。
- **Untracked File Warning**: 如果检测到有新的文件变更未被记录进 Issue，Linter 会发出警告，提示运行 `sync-files`。
- **Progress Consistency**: 检查 Checkbox 的勾选情况是否与关联的测试或代码提交相匹配。

## 2. 质量门禁 (Stage Gates)

随着 Issue 从 `draft` 流转到 `done`，系统对其完整性的要求逐步提高。Linter 会根据当前的 `stage` 应用不同的检查策略。

| Stage | 检查严格度 | 要求 |
| :--- | :--- | :--- |
| `draft` | 宽松 (Loose) | 只要 YAML 格式正确即可。允许缺字段。 |
| `doing` | 标准 (Standard) | 必须有 Checkbox。`files` 列表不能为空。 |
| `review` | 严格 (Strict) | Checkbox 必须全勾选。必须有 PR 链接（如有）。 |
| `done` | 冻结 (Frozen) | 文件不可再被修改（除迁移状态外）。 |

这意味着，你可以在草稿阶段随意涂鸦，但在申请合并代码（Submit）时，必须补全所有的元数据和文档。这强迫开发者在交付前整理思路，而不是之后补票。

## 3. 自动化修复

`monoco issue lint --fix` 提供了一定程度的自动修复能力：
- 自动修正格式错误的 YAML。
- 自动移除 `files` 列表中不存在的文件路径。
- 自动根据当前时间更新 `updated_at` 字段。
