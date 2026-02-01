---
id: FIX-0004
uid: 161b33
type: fix
status: closed
stage: done
title: 放宽技术 Issue 的 i18n 语言检测
created_at: '2026-02-01T22:11:46'
updated_at: '2026-02-01T22:34:33'
parent: EPIC-0027
dependencies: []
related: []
domains:
- IssueGovernance
tags:
- '#EPIC-0027'
- '#FIX-0004'
files:
- monoco/features/i18n/core.py
- tests/features/i18n/test_language_detection.py
criticality: high
opened_at: '2026-02-01T22:11:46'
closed_at: '2026-02-01T22:34:33'
solution: implemented
---

## FIX-0004: 放宽技术 Issue 的 i18n 语言检测

## Objective
放宽对技术性 Issue 的 i18n 语言检测规则。目前 Linter过于严格，将包含大量英文技术术语（如 CLI, API, Kubernetes 等）的中文 Issue 误判为英文。

## Acceptance Criteria
- [x] **Heuristic Adjustment**: 调整语言检测启发式算法，提高对中英混排内容的容忍度。
- [x] **Allowlist**: 允许常见的技术术语不计入英文单词计数。
- [x] **Threshold Tuning**: 将误判阈值调整到合理范围。

## Technical Tasks
- [x] **CHORE-Tune-Detector**: 调整 `monoco-linter` 中的语言检测逻辑。
- [x] **TEST-Verify-Cases**: 验证 `FIX-0003` 等 Issue 不再被误报。

## Implementation Details

### 1. 技术术语 Allowlist (`TECHNICAL_TERMS_ALLOWLIST`)
在 `monoco/features/i18n/core.py` 中添加了一个包含 400+ 常见技术术语的 allowlist，包括：
- CLI/Shell 术语 (cli, api, bash, shell, terminal 等)
- 云/容器技术 (kubernetes, k8s, docker, aws, gcp 等)
- DevOps/CI/CD 术语 (ci, cd, pipeline, git, github 等)
- 编程语言 (python, javascript, typescript, go, rust 等)
- Web 框架 (react, vue, angular, django, flask 等)
- 数据库 (sql, mysql, postgresql, mongodb, redis 等)
- 测试术语 (pytest, jest, unittest, mock, coverage 等)
- 架构模式 (microservice, rest, graphql, grpc 等)
- 安全术语 (oauth, jwt, ssl, tls, encryption 等)
- AI/ML 术语 (llm, nlp, tensorflow, pytorch 等)

### 2. 启发式算法优化 (`detect_language`)
- **代码块过滤**: 移除 ``` 代码块和 `` 内联代码，避免代码中的英文关键字干扰检测
- **URL 过滤**: 移除 URL 链接
- **Issue ID 过滤**: 移除 格式的 Issue ID
- **CJK 阈值调整**: 从 5% 降低到 3%，提高中文检测灵敏度
- **技术术语排除**: 在判断英文内容时，将 allowlist 中的技术术语从计数中排除
- **非技术词汇要求**: 判断为英文需要至少 10 个非技术英文单词

### 3. 新增测试
创建了 `tests/features/i18n/test_language_detection.py`，包含：
- 纯中文/英文内容检测测试
- 中文+技术术语检测测试（核心场景）
- FIX-0003 场景回归测试
- 代码为主内容的处理测试
- Allowlist 内容验证测试

## Review Comments
- 实现通过 11 个单元测试验证
- FIX-0003 场景不再被误判为英文
- 代码块和 Issue ID 被正确过滤，避免干扰检测
