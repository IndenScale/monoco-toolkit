# Monoco Issue 配置指南

Monoco Issue System 是高度可配置的。通过在 `.monoco/workspace.yaml` 或 `.monoco/project.yaml` 中定义配置，你可以完全控制 Issue 的类型、状态、阶段以及流转规则。

## 配置结构

配置位于 `issue` 节点下。

```yaml
issue:
  types: [...] # 定义 Issue 类型
  statuses: [...] # 定义物理状态
  stages: [...] # 定义逻辑阶段
  solutions: [...] # 定义关闭时的解决方案
  workflows: [...] # 定义状态转移规则
```

## 1. Issue 类型 (Types)

定义系统中存在的 Issue 种类。

```yaml
types:
  - name: feature # 内部 ID (全小写)
    label: Feature # 显示名称
    prefix: FEAT # ID 前缀 (e.g. FEAT-001)
    folder: Features # 存储目录名
    description: '...' # 描述
```

## 2. 状态与阶段 (Status & Schema)

定义状态机的词汇表。

```yaml
# 物理状态 (通常不建议修改，因为涉及文件系统结构)
statuses:
  - open
  - closed
  - backlog

# 逻辑阶段 (自由定义)
stages:
  - draft
  - doing
  - review
  - done
  - freezed

# 解决方案 (用于 Close 动作)
solutions:
  - implemented
  - cancelled
  - wontfix
  - duplicate
```

## 3. 工作流 (Global Workflows)

定义状态转移矩阵。每一项代表一个可执行的动作 (Action)。

```yaml
workflows:
  - name: start # 动作 ID
    label: Start # UI 显示标签
    icon: '$(play)' # UI 图标 (VS Code codicons)

    # --- 触发条件 ---
    from_status: open # 仅在 open 状态下可用
    from_stage: draft # 仅在 draft 阶段可用

    # --- 目标状态 ---
    to_status: open # 保持 open 状态
    to_stage: doing # 变更为 doing 阶段

    # --- 副作用 ---
    command_template: 'monoco issue start {id}' # 执行的 CLI 命令
    description: 'Start working on the issue'

  - name: close_done
    label: Close
    icon: '$(close)'
    from_status: open
    from_stage: done
    to_status: closed
    to_stage: done
    required_solution: implemented # 此动作要求必须提供 solution=implemented
```

### 必填字段说明

- **Status/Stage**: 如果通过 Action 变更状态，必须显式指定 `to_status` 和 `to_stage`。
- **Universal Actions**: 如果 `from_status` 和 `from_stage` 为空，则该动作在任何状态下都可见（通常用于触发 Agent 任务，如 "Investigate"）。

## 默认配置参考

Monoco 内置了一套标准的研发流配置。你可以通过查看 `monoco/features/issue/engine/config.py` 获取完整的默认值，或者直接在 `workspace.yaml` 中覆盖它。
