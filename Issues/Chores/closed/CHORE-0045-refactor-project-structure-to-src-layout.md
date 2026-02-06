---
id: CHORE-0045
uid: 1c6018
type: chore
status: closed
stage: done
title: Refactor project structure to src layout
created_at: '2026-02-06T05:40:25'
updated_at: '2026-02-06T05:50:00'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0045'
- '#EPIC-0000'
files:
- pyproject.toml
- monoco.spec
- scripts/build_cli.sh
- src/monoco/main.py
- Issues/Chores/open/CHORE-0045-refactor-project-structure-to-src-layout.md
criticality: low
solution: implemented
opened_at: '2026-02-06T05:40:25'
---

## CHORE-0045: Refactor project structure to src layout

## 目标
将项目结构从扁平布局重构为 src 布局（src/monoco/），以符合更好的 Python 打包实践。

## 验收标准
- [x] 代码目录移至 src/monoco/
- [x] pyproject.toml 更新为 packages = ["src/monoco"]
- [x] monoco.spec 更新为 src/monoco/main.py
- [x] build_cli.sh 更新为正确的路径
- [x] main.py 更新为在正确的相对路径找到 pyproject.toml
- [x] 构建成功通过

## 技术任务
- [x] 创建 src/ 目录并将 monoco/ 移入
- [x] 更新 pyproject.toml 包路径
- [x] 更新 monoco.spec Analysis 入口点
- [x] 更新 scripts/build_cli.sh SRC_DIR 和 pyinstaller 路径
- [x] 更新 src/monoco/main.py pyproject.toml 查找（增加一级父目录）
- [x] 运行构建验证
- [x] 更新 issue 状态为已关闭

## Review Comments
成功完成。构建已验证，所有核心测试通过。
