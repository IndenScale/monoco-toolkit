---
id: FIX-0016
uid: 8760f5
type: fix
status: closed
stage: done
title: Fix Pydantic V2 migration warnings
created_at: '2026-01-29T16:53:41'
updated_at: 2026-01-29 17:01:17
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0016'
files: []
opened_at: '2026-01-29T16:53:41'
closed_at: '2026-01-29T17:00:57'
solution: implemented
---

## FIX-0016: Fix Pydantic V2 migration warnings

## 目标
移除 Toolkit 中 pytest 执行期间的 Pydantic V2 警告。
需要修复的关键警告：
1. `PydanticDeprecatedSince20`: `Session` 模型中基于类的配置。
2. `PydanticSerializationUnexpectedValue`: `IssueMetadata` 的枚举序列化警告。

## 验收标准
- [x] 运行 `pytest` 时所有 Pydantic 警告已解决。
- [x] 测试中没有回归。

## 技术任务

- [x] 在 `monoco/features/scheduler/session.py` 中将 `class Config` 替换为 `model_config = ConfigDict(...)`。
- [x] 在 `IssueMetadata.normalize_fields` 中强制枚举强制转换，以防止 `PydanticSerializationUnexpectedValue` 警告。
- [x] 在 `IssueMetadata` 模型配置中启用 `validate_assignment=True`。

## 评审意见
- 验证了警告在本地已消失。
- 验证了 `repro_warning.py` 行为正确。

## Review Comments

- [x] Self-Review
