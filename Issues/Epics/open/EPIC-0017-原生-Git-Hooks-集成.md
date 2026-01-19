---
id: EPIC-0017
uid: 89dd60
type: epic
status: open
stage: doing
title: 原生 Git Hooks 集成
created_at: '2026-01-19T00:27:09'
opened_at: '2026-01-19T00:27:09'
updated_at: '2026-01-19T00:27:09'
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0017'
progress: 4/4
files_count: 0
---

## EPIC-0017: 原生 Git Hooks 集成

## 目标
<!-- 清晰地描述“为什么”和“是什么”。关注价值。 -->
实现 Monoco 的原生 Git Hooks 集成，以自动化工作流（如提交前的 Issue 检查）。

## 验收标准
<!-- 定义成功的二进制条件。 -->
- [ ] 能够在初始化时自动安装 Hooks
- [ ] Hooks 可以触发 `monoco issue lint`

## 技术任务
<!-- 分解为原子步骤。使用嵌套列表表示子任务。 -->

<!-- 状态语法： -->
<!-- [ ] 待办 -->
<!-- [/] 正在进行 -->
<!-- [x] 已完成 -->
<!-- [~] 已取消 -->
<!-- - [ ] 父任务 -->
<!--   - [ ] 子任务 -->

- [x] 实现 Git Hooks 机制

## 评审意见
<!-- 评审/完成阶段需要。在此记录评审反馈。 -->
