---
id: FEAT-0105
uid: ef7b66
parent: EPIC-0000
type: feature
status: closed
stage: done
title: Domain Ontology Management with Aliasing and Linting
created_at: '2026-01-25T14:45:14'
opened_at: '2026-01-25T14:45:14'
updated_at: '2026-01-25T22:53:58'
closed_at: '2026-01-25T22:53:58'
solution: implemented
isolation:
  type: branch
  ref: feat/feat-0105-domain-ontology-management-with-aliasing-and-linti
  created_at: '2026-01-25T14:45:34'
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0105'
files: []
---

## FEAT-0105: Domain Ontology Management with Aliasing and Linting

## Objective
目前 Monoco Issue 中的 `domains` 字段仅为简单的字符串列表，缺乏统一的词表管理和规范约束。Agent 或用户可能会混用别名（如 `auth` vs `authentication`），导致领域分类混乱。

本需要旨在建立一套轻量级的 **领域本体 (Domain Ontology)** 系统，支持：
1. **结构化定义**：在配置文件中定义规范的领域词表（支持层级 `backend.auth`）。
2. **别名机制 (Paraphrasing)**：支持定义别名（如 `login` -> `backend.auth`），允许用户使用习惯用语。
3. **Linting & Auto-fix**：Linter 扫描 Issue 时，自动检查 `domains` 合法性，并建议或自动将别名替换为规范名。

## Acceptance Criteria
- [x] 能够通过 `monoco issue domain` 命令查看和管理领域词表（至少支持 List）。
- [x] 支持在配置中定义 Domain，包含 `name`, `description`, `aliases`。
- [x] `monoco issue lint` 能够识别非标准 Domain。
- [x] `monoco issue lint` 能够识别 Alias 并警告（建议替换）。
- [x] `monoco issue lint --fix` 能够自动将 Alias 替换为 Canonical Domain。

## Technical Tasks
- [x] **Config Layer**:
    - [x] 修改 `monoco/core/config.py`，新增 `DomainConfig` 和 `DomainItem` 模型。
    - [x] 扩展 `MonocoConfig` 包含 `domains` 列表。
- [x] **Domain Service**:
    - [x] 实现 `DomainService` 类，负责解析 Config，构建 Alias -> Canonical 的映射表。
    - [x] 实现模糊匹配逻辑（可选）。
- [x] **CLI Layer**:
    - [x] 新增 `monoco/features/issue/domain_commands.py`。
    - [x] 注册 `monoco issue domain` 子命令组 (`list`, `check`).
- [x] **Linter Integration**:
    - [x] 修改 `IssueValidator`，注入 `DomainService`。
    - [x] 实现 `validate_domains` 规则：Unknown Domain (Warn), Alias Usage (Warn + Fixable)。
    - [x] 修改 `linter.py` 中的 `run_lint` 支持 Domain Auto-fix。

## Review Comments

- Verified `monoco issue domain list` command functionality.
- Domain check and Aliasing feature verified.
