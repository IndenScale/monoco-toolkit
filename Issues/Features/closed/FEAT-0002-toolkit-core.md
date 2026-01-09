---
parent: EPIC-0001
id: FEAT-0002
type: feature
status: closed
title: "Implement Toolkit Core Infrastructure"
created_at: 2026-01-08
solution: implemented
tags: [toolkit, infra, architecture]
---

parent: EPIC-0001

## FEAT-0002: Toolkit Core Infrastructure

## Objective

搭建 Monoco Toolkit 的基础骨架，确保开发体验 (DX) 和运行时基础能力。

## Acceptance Criteria

1. **Project Structure**: `Toolkit/` 目录下包含完整的 PDM 项目结构 (`pyproject.toml`, `src/monoco`).
2. **CLI Entrypoint**: `monoco` 命令可在本地 shell 中执行 (`pip install -e .`)。
3. **Output System**: 实现 `monoco.core.output` 模块，支持 Human (Rich Table) 和 Agent (JSON) 两种输出模式的切换。
4. **Configuration**: 实现基础配置加载逻辑 (e.g. searching for `.monoco/config.yaml` or env vars).

## Technical Tasks

- [x] Initialize PDM project in `Toolkit/`.
- [x] Implement `monoco.main` utilizing `Typer`.
- [x] Implement `monoco.core.output.print_output(data, format=...)`.
- [x] Setup proper `setup.py` / `pyproject.toml` entry_points.
- [x] Implement `monoco.core.config` with Pydantic and PyYAML.
