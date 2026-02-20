---
id: FEAT-0206
uid: 40b1d1
type: feature
status: open
stage: doing
title: 将 monoco sync 重构为 monoco install，支持全局/项目安装和分模块安装
created_at: '2026-02-20T18:28:50'
updated_at: '2026-02-20T18:29:08'
parent: EPIC-0000
dependencies: []
related: []
domains:
- cli
- core
tags:
- '#EPIC-0000'
- '#FEAT-0206'
files:
- src/monoco/core/sync.py
- src/monoco/main.py
- src/monoco/core/skills.py
- src/monoco/core/config.py
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-20T18:28:50'
---

## FEAT-0206: 将 monoco sync 重构为 monoco install，支持全局/项目安装和分模块安装

## Objective

当前 `monoco sync` 命令语义不够清晰，且不支持细粒度的安装控制。本功能将其重构为 `monoco install`，提供更符合直觉的 CLI 语义，并支持：

1. **全局/项目双作用域安装** - 允许用户将通用的 roles、skills 安装到全局，项目特定的保留在项目
2. **分模块安装** - 支持只安装特定模块（如仅 roles、仅 hooks）
3. **向后兼容** - 保留 `monoco sync` 作为 `monoco install --all --project` 的别名

## Acceptance Criteria

- [ ] CLI 命令 `monoco install` 可用，支持 `[modules...]` 位置参数
- [ ] 支持 `-g/--global` 和 `-p/--project` 作用域选项（默认项目）
- [ ] 支持 `--all` 安装所有模块（默认行为）
- [ ] 模块依赖自动解析（如 workflows 依赖 skills）
- [ ] 全局安装时跳过 git hooks（hooks 与仓库绑定）
- [ ] `monoco sync` 作为 `monoco install --all --project` 的别名保留
- [ ] `monoco uninstall` 同步支持全局/项目作用域

## Technical Tasks

### Phase 1: CLI 重构
- [ ] 将 `src/monoco/core/sync.py` 重命名为 `install.py`
- [ ] 重构 `install_command` 参数：添加 `modules` 位置参数和 `--global/--project` 选项
- [ ] 保留 `sync_command` 作为别名，调用 `install --all --project`
- [ ] 更新 `main.py` 中的命令注册

### Phase 2: 作用域支持
- [ ] 实现全局路径解析（`~/.monoco/`, `~/.config/agents/`）
- [ ] 修改 `SkillManager.distribute()` 支持目标路径参数
- [ ] 修改 `PromptInjector` 支持全局 AGENTS.md 路径
- [ ] 实现全局/项目配置合并策略

### Phase 3: 模块选择与依赖
- [ ] 定义模块枚举：`roles`, `skills`, `workflows`, `hooks`, `prompts`
- [ ] 实现模块依赖图（如 workflows → skills → roles）
- [ ] 实现拓扑排序确保正确安装顺序
- [ ] 全局安装时自动排除 hooks 模块

### Phase 4: Uninstall 同步
- [ ] 重构 `uninstall_command` 支持 `--global/--project`
- [ ] 支持按模块卸载

## Design Notes

### 命令示例

```bash
# 项目级完整安装（当前 sync 行为）
monoco install
monoco install --all
monoco sync  # 别名

# 仅安装特定模块
monoco install roles skills
monoco install hooks

# 全局安装
monoco install -g roles skills
monoco install --global  # hooks 被跳过
```

### 路径映射

| 类型 | 项目路径 | 全局路径 |
|------|----------|----------|
| roles | `./.monoco/roles/` | `~/.monoco/roles/` |
| skills | `./.agents/skills/` | `~/.config/agents/skills/` |
| hooks | `./.git/hooks/` | N/A |
| prompts | `./AGENTS.md` | `~/.config/agents/AGENTS.md` |
