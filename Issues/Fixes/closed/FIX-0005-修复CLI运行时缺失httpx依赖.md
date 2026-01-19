---
id: FIX-0005
uid: fix-005-httpx
type: fix
status: closed
stage: done
title: 修复 CLI 运行时缺失 httpx 依赖
created_at: '2026-01-13T16:35:15'
opened_at: '2026-01-13T16:35:15'
updated_at: '2026-01-13T16:41:12'
closed_at: '2026-01-13T16:41:12'
solution: implemented
parent: null
dependencies: []
related: []
domains: []
tags:
- '#FIX-0005'
- bug
- cli
- dependency
---

## FIX-0005: 修复 CLI 运行时缺失 httpx 依赖

## Problem

用户在运行 `monoco` CLI 命令时遭遇报错，提示缺少 `httpx` 模块。
这导致无法使用 CLI 进行 Issue 管理等操作。

## Root Cause

`httpx` 库在 `monoco` 核心逻辑（如 Telemetry）中被引用，但可能未在环境中正确安装，或在 `pyproject.toml` 中的依赖声明未被正确解析/同步到当前环境。

## Solution

1. **Lazy Import**: 将 `monoco/core/telemetry.py` 中的 `import httpx` 改为在该方法调用时懒加载。
2. **Optional Dependency**: 捕获 `ImportError`，如果环境中没有 `httpx`，则自动静默跳过遥测上报，不阻塞 CLI 核心功能。

已通过修改 `monoco/core/telemetry.py` 实现上述修复。

## Implementation Details

```python
# monoco/core/telemetry.py

def capture(self, ...):
    try:
        import httpx
        httpx.post(...)
    except ImportError:
        pass # Telemetry is optional
```

## Acceptance Criteria

- [x] CLI 不再因为缺少 `httpx` 而崩溃。
- [x] 在没有 `httpx` 的环境下，遥测逻辑被安全忽略。

## Technical Tasks

- [x] 实现 `monoco/core/telemetry.py` 的 Lazy Import 逻辑。
- [x] 手动验证卸载 `httpx` 后的运行情况。

## Review Comments

- [x] Self-Review
