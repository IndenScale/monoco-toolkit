---
id: CHORE-0006
uid: 0bb9a0
type: chore
status: closed
stage: done
title: 调研增强型 Issue 模板
created_at: "2026-01-17T09:55:05"
opened_at: "2026-01-17T09:55:05"
updated_at: "2026-01-17T10:25:00"
closed_at: "2026-01-17T10:25:00"
parent: null
solution: implemented
dependencies: []
related: []
tags: []
---

## CHORE-0006: 调研增强型 Issue 模板

## Objective

分析当前 Issue 模板系统的局限性，并提出一种“自文档化”结构，使 Agent 无需严重依赖外部手册即可理解系统。

核心关注点：

1. **字段可见性**：`parent`、`solution` 等字段在为空时被隐藏。
2. **结构引导**：`Technical Tasks` 和 `Acceptance Criteria` 缺乏示例或层级结构。
3. **状态验证**：在状态流转时强制检查特定字段的完整性。

## Analysis

### 1. 当前局限性

- **隐式字段**：YAML Frontmatter 仅转储非空字段。
- **扁平结构**：缺乏嵌套任务和详细验收标准的引导。
- **语法不一致**：代码库中 Parser 支持 `[+]` 作为废弃，但 Validator 报错。

### 2. 提案：自文档化模板

我们应该在生成的 Markdown 中注入 **注释** 作为原位文档。

#### A. 交互式 Frontmatter

使用注释显示可用但未设置的字段。

```yaml
id: ISSUE-001
# ...
# parent: <EPIC-ID>  # 可选：父 Issue ID (Epic/Story)
# solution: null     # 必需：关闭状态时需要填写 (completed, won fix, etc.)
```

#### B. 指导性正文

注入 HTML 注释 `<!-- ... -->` 提供上下文。

```markdown
## Objective

<!-- 清晰描述“为什么”和“做什么”。关注用户价值。 -->

## Acceptance Criteria

<!-- 定义成功的二元条件。 -->

- [x] 验收标准 1
- [x] 验收标准 2

## Technical Tasks

<!-- 将任务分解为原子步骤。使用嵌套列表表示子任务。 -->

<!-- 任务状态语法示例（提案）： -->

[ ] 待办任务 (To Do)
[/] 进行中 (Doing) <!-- 建议：使用斜杠代表进展 -->
[x] 已完成 (Done)
[~] 已废弃 (Cancelled) <!-- 修正：原 [+] 为反使用 Add 语义，改为 [~] -->

<!-- 层级结构示例： -->

[ ] 父任务 A
[ ] 子任务 A.1 (缩进 2 空格)
[ ] 子任务 A.2
```

### 3. 提案：严格状态校验

我们应该将校验逻辑从“指南”升级为“代码强制”。

| 流转 (Transition) | 要求 (Requirement) | 校验器逻辑 (Validator Logic)                            |
| :---------------- | :----------------- | :------------------------------------------------------ |
| `* -> DOING`      | 定义任务           | `Technical Tasks` 章节必须包含至少一个复选框 `[ ]`。    |
| `DOING -> REVIEW` | 任务全完           | `Technical Tasks` 中的所有复选框必须为非空状态 (x, -)。 |
| `REVIEW -> DONE`  | 验收通过           | `Acceptance Criteria` 中的所有复选框必须为 `[x]`。      |

## Plan

1. [x] **修复语法一致性**：统一 `parser.py` 和 `validator.py` 对 `[+]` (Abandoned) 的支持。
2. [x] **原型模板**：修改 `core.py` 以生成增强型模板。
3. [x] **实现校验器**：更新 `validator.py`，根据状态解析并检查特定章节。

## Technical Tasks

- [x] 统一 Checkbox 状态定义 (`parser` vs `validator`)。
- [x] 修改 `monoco.features.issue.core.create_issue_file` 使用新的模板结构。
- [x] 在 `monoco.features.issue.validator.IssueValidator` 中添加 `validate_state_requirements`。

## Review Comments

- Reviewed self-documenting templates.
- Verified strict validation logic.
