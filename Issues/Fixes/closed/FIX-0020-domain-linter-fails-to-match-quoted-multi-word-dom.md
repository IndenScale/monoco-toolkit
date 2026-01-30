---
id: FIX-0020
uid: a4d983
type: fix
status: closed
stage: done
title: Domain linter fails to validate domain name strict matching
created_at: '2026-01-30T08:37:00'
updated_at: 2026-01-30 08:52:52
parent: EPIC-0001
dependencies: []
related:
- FEAT-0114
domains:
- IssueTracing
- Guardrail
tags:
- '#EPIC-0001'
- '#FIX-0020'
- '#FEAT-0114'
files:
- monoco/features/issue/linter.py
- monoco/features/issue/validator.py
- tests/features/issue/test_linter_strict.py
- tests/features/issue/test_linter_domain_fix.py
opened_at: '2026-01-30T08:37:00'
closed_at: '2026-01-30T08:52:51'
solution: implemented
---

## FIX-0020: Domain linter fails to validate domain name strict matching

## Objective
修复 Domain linter 的校验逻辑，确保 Issue 中 `domains` 字段的值必须与 Domain 定义严格一致。

## Design Decision: PascalCase (No Spaces)

**Domain 名称必须使用 PascalCase 无空格格式。**

理由：
1. **机器优先**：Monoco 是 Agent-Native 工具，机器处理优先于人类阅读
2. **工具链友好**：文件名、URL、命令行、代码标识符都无需转义
3. **一致性**：与 Issue ID（`FEAT-0001`）、Type（`Feature`）风格一致
4. **扩展性**：未来支持 `Domain.Subdomain` 层级（`Core.Guardrail`）

### 命名规范

| 格式 | 示例 | 状态 |
|------|------|------|
| PascalCase | `IssueTracing`, `AgentOnboarding` | ✅ 标准 |
| Title Case | `Issue Tracing`, `Agent Onboarding` | ❌ 不允许 |
| kebab-case | `issue-tracing`, `agent-onboarding` | ❌ 不允许 |
| snake_case | `ISSUE_TRACING`, `AGENT_ONBOARDING` | ❌ 不允许 |

### 校验规则

Domain 名称必须同时满足：
1. **格式**：PascalCase，无空格
2. **文件名匹配**：`Issues/Domains/{DomainName}.md` 存在
3. **Heading 匹配**：文件内 Level 1 Heading 为 `# {DomainName}`

### 当前系统中的 Domain

```
Issues/Domains/
├── AgentOnboarding.md    → 域名: AgentOnboarding
├── AgentScheduling.md    → 域名: AgentScheduling
├── Guardrail.md          → 域名: Guardrail
└── IssueTracing.md       → 域名: IssueTracing
```

## Bug Description

### 当前行为
```yaml
# Issue frontmatter
domains:
- "Guardrail"        # ❌ 错误：带引号（虽然解析后值正确，但风格不统一）
- "Issue Tracing"    # ❌ 错误：带空格，无法匹配 IssueTracing.md
```

Linter 报错信息混乱：
- 提示 `"Guardrail"` 不在列表中
- 但建议列表里却包含 `Guardrail`

### 期望行为
```yaml
# Issue frontmatter
domains:
- Guardrail      # ✅ 正确
- IssueTracing   # ✅ 正确
```

## Acceptance Criteria
- [x] Linter 校验 domain 格式必须为 PascalCase
- [x] Linter 错误信息明确提示格式要求和可用列表
- [x] 提供 `--fix` 自动修复：
  - [x] 去除引号
  - [x] 空格转为 PascalCase（`Issue Tracing` → `IssueTracing`）
- [x] 更新文档说明 Domain 命名规范

## Technical Tasks

### 1. 问题定位
- [x] 检查 `validator.py` 或 `linter.py` 中 domain 校验逻辑
- [x] 确认 YAML 解析后 domain 值的类型

### 2. 修复校验逻辑
- [x] 添加 `is_pascal_case()` 校验函数
- [x] 规范化 domain 值（去除引号、trim 空格）
- [x] 与 `Issues/Domains/` 下的文件名列表严格比较
- [x] 校验 Heading 匹配（可选）

### 3. 改进错误信息
- [x] 格式错误："Domain 'X' must be PascalCase (e.g., 'IssueTracing')"
- [x] 不存在："Domain 'X' not found. Available: AgentOnboarding, AgentScheduling, Guardrail, IssueTracing"

### 4. 自动修复
- [x] `to_pascal_case()`：去除引号、首字母大写、去空格后驼峰
- [x] `--fix` 集成

### 5. 文档更新
- [x] 更新 SKILL.md 说明 Domain 命名规范
- [x] 更新 AGENTS.md 添加 Domain 创建指南

## Related
- Parent: EPIC-0001
- Related: FEAT-0114（触发此 bug 的 Issue）

## Review Comments
- 已实现跨文件的重复 ID 校验。
- 已实现文件名（ID 与 Slug）与 Frontmatter 的一致性校验。
- 已实现 Domain 的 PascalCase 强校验与自动修复。
- 已补充单元测试 `test_linter_strict.py` 和 `test_linter_domain_fix.py`。
- 已更新相关技能文档和 Agent 指引。
