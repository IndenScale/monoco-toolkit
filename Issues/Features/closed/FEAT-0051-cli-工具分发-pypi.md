---
id: FEAT-0051
uid: 40a9be
type: feature
status: closed
stage: done
title: CLI 工具分发 - PyPI
created_at: "2026-01-13T13:58:29"
opened_at: "2026-01-13T14:43:49"
updated_at: "2026-01-13T14:43:55"
closed_at: "2026-01-13T14:43:55"
parent: EPIC-0009
solution: implemented
dependencies: []
related: []
tags: []
---

## FEAT-0051: CLI 工具分发 - PyPI

## Objective

建立 Monoco Toolkit 的 PyPI 自动发布流水线，使用户能够通过 `pip install monoco-toolkit` 一键安装 CLI 工具。复用 Typedown 的 Trusted Publishing 机制，确保发布流程安全、自动化且可追溯。

## Acceptance Criteria

- [x] **自动化发布**: Git Tag (`v*`) 触发自动构建并发布至 PyPI。
- [x] **质量保障**: 发布前自动执行测试套件与 Issue Lint 校验。
- [x] **元数据完整**: PyPI 页面展示完整的项目信息（描述、关键词、许可证、链接）。
- [x] **Trusted Publishing**: 使用 GitHub OIDC 认证，无需手动管理 API Token。
- [x] **版本一致性**: Git Tag 版本与 `pyproject.toml` 版本保持同步。（已通过 v0.1.0 验证）

## Technical Tasks

- [x] 创建 `.github/workflows/publish-pypi.yml` 工作流。
- [x] 完善 `pyproject.toml` 元数据（许可证、分类器、项目链接）。
- [x] **创建 GitHub 仓库并完成初始推送** (`IndenScale/monoco-toolkit`)。
- [x] 在 PyPI 配置 Trusted Publishing (需要项目管理员登录 PyPI 官网操作)。
- [x] 验证发布流程: 创建 v0.1.0 Tag 并观察 CI 执行。
- [x] 更新 `README.md` 添加安装说明 (`pip install monoco-toolkit`)。
- [x] 文档化发布流程 (CONTRIBUTING.md 或 docs/)。

## Review Comments

- [x] Self-Review
