# 02. 记录系统：Issue Ticket

## 摘要

Issue Ticket 是 AHP 的基础数据单元，采用 Markdown + YAML 的本地文本化格式，作为任务代理协作的共享上下文载体。本文定义 Issue Ticket 的结构、协作模型、关联机制，以及其与 Git 工作流的集成方式。

---

## 1. 设计哲学：文本即记录

### 1.1 为什么选择本地文本

AHP 采用文件系统作为数据存储层，而非数据库或 Web 服务：

| 维度 | 文本文件 | 数据库/Web 服务 |
|------|----------|-----------------|
| **版本控制** | 原生支持 Git 历史追溯 | 需额外实现 |
| **离线可用** | 完全离线 | 依赖网络连接 |
| **可观测性** | 文件即状态，可直接查看 | 需查询接口 |
| **工具生态** | 通用编辑器、grep、awk | 专用客户端 |
| **长期存档** | 纯文本，无格式过时风险 | 需迁移维护 |

### 1.2 Markdown + YAML 分离

每个 Issue Ticket 是一个 Markdown 文件，采用 YAML Front Matter 存储结构化数据：

```markdown
---
id: FEAT-0123
type: feature
status: open
---

# 实现用户登录功能

## 背景
...

## 任务清单
- [x] 设计数据库 Schema
- [ ] 实现登录 API
```

**分离原则**：
- **YAML Front Matter**：机器消费的结构化字段（状态、元数据、关联）
- **Markdown Body**：人类阅读的自然语言描述（需求、讨论、决策）

---

## 2. 协作模型：Draft → Doing → Review → Done

### 2.1 状态机定义

Issue Ticket 的生命周期遵循四阶段模型：

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  draft  │───►│  doing  │───►│ review  │───►│  done   │
│ (草稿)   │    │ (进行中) │    │ (审查中) │    │ (已完成) │
└────┬────┘    └────┬────┘    └────┬────┘    └─────────┘
     │              │              │
     └──────────────┴──────────────┘
              (可回退到 draft)
```

| 状态 | 含义 | 准入条件 | 准出条件 |
|------|------|----------|----------|
| **draft** | 待启动的工作单元 | Issue 已创建 | 智能体接受任务 |
| **doing** | 正在实现中 | 前置依赖满足 | 代码实现完成 |
| **review** | 待审查验证 | 自检清单完成 | 审查通过 |
| **done** | 已完成并归档 | 审查通过 | - |

### 2.2 状态转换触发

状态转换由特定事件触发：

| 转换 | 触发事件 | 系统行为 |
|------|----------|----------|
| `draft → doing` | 智能体 `start` 命令 | 创建工作分支，加载上下文 |
| `doing → review` | 智能体 `submit` 命令 | 运行预提交检查 |
| `review → done` | 审查者批准 | 合并到主干，清理分支 |
| `review → doing` | 审查者驳回 | 返回修改，记录反馈 |
| `* → draft` | 任务取消或重置 | 保留历史，重置状态 |

### 2.3 与 Git 的集成

状态映射到 Git 工作流：

```
draft    →  Issue 文件存在于工作目录
          （Git 状态：未追踪或已提交）

doing    →  开发分支活跃
          （Git 状态：branch 存在，有未提交变更）

review   →  PR/MR 已创建（或等效的本地标记）
          （Git 状态：分支已推送，等待合并）

done     →  已合并到主干，Issue 归档
          （Git 状态：commit 在主分支，Issue 移动至归档目录）
```

---

## 3. Schema 设计

### 3.1 核心字段

#### 身份标识

```yaml
id: FEAT-0123           # 人类可读标识
uid: uuid-v4-string     # 机器唯一标识
type: feature           # issue 类型
```

**类型枚举**：
- `feature`：新功能
- `fix`：缺陷修复
- `chore`：维护任务
- `docs`：文档更新
- `refactor`：代码重构
- `test`：测试补充
- `spike`：技术调研
- `arch`：架构决策

#### 生命周期状态

```yaml
status: doing           # 当前状态
stage: implementing     # 执行阶段细化
```

**stage 细分**（可选）：
- `investigating`：调研分析
- `designing`：设计阶段
- `implementing`：实现阶段
- `reviewing`：审查阶段
- `verifying`：验证阶段

#### 内容描述

```yaml
title: "实现用户登录功能"
description: |
  作为用户，我希望能够使用邮箱和密码登录系统。
---

## 背景
...

## 目标
...

## 验收标准
- [ ] 标准 1
- [ ] 标准 2
```

### 3.2 爆炸范围记录

`files` 字段记录 Issue 涉及的文件，用于：
- 快速定位相关代码
- 变更影响分析
- 自动同步到 Git

```yaml
files:
  - src/auth/login.py
  - src/auth/models.py
  - tests/auth/test_login.py
```

**自动更新**：通过 `monoco issue sync-files` 命令，系统基于 `git diff` 自动更新此列表。

---

## 4. 关联建模

### 4.1 关联类型

Issue Ticket 支持多种关联机制：

| 关联类型 | 字段 | 用途 | 示例 |
|----------|------|------|------|
| **父子** | `parent` | 分解大任务 | Epic → Story |
| **依赖** | `depends_on` | 执行顺序约束 | A 依赖 B 完成 |
| **标签** | `tags` | 分类与筛选 | `priority:high`, `area:auth` |
| **Wiki 链接** | `[[ID]]` | 知识关联 | `[[ARCH-001]]` |

### 4.2 依赖语义

```yaml
depends_on:
  - FEAT-0120      # 依赖其他 Issue
  - "config:db"    # 依赖配置就绪
```

**依赖解析规则**：
- 被依赖项必须达到 `done` 状态，才能启动依赖项
- 循环依赖被禁止（验证时检测）
- 软依赖（建议性）与硬依赖（强制性）区分

### 4.3 Wiki 链接语法

在 Markdown Body 中使用双括号语法创建关联：

```markdown
本功能依赖 [[ARCH-001]] 中定义的认证架构。
相关实现参考 [[FEAT-0120]] 的用户模型。
```

渲染时解析为可点击链接。

---

## 5. 里程碑与验收标准

### 5.1 Stage 作为里程碑

每个 `stage` 代表一个里程碑，具有独立的验收标准：

```yaml
phases:
  - name: design
    title: "设计阶段"
    status: done
    acceptance_criteria:
      - criterion: "API 设计文档"
        verification: "file_exists:docs/api/login.yaml"
      
  - name: implementation
    title: "实现阶段"
    status: doing
    acceptance_criteria:
      - criterion: "登录 API 实现"
        verification: "test_pass:tests/api/test_login.py"
```

### 5.2 验收标准语法

| 验证类型 | 语法 | 说明 |
|----------|------|------|
| 测试通过 | `test_pass:<path>` | 指定测试通过 |
| 文件存在 | `file_exists:<path>` | 文件存在于仓库 |
| 代码审查 | `code_review:<path>` | 审查标记完成 |
| Lint 通过 | `lint_clean:<path>` | 无风格问题 |
| 自定义 | `custom:<script>` | 执行验证脚本 |

### 5.3 Checklist 语义

Checklist 是细粒度的可验证任务：

```yaml
checklist:
  - id: "chk-001"
    item: "设计数据库 Schema"
    checked: true
    verification:
      type: "test"
      target: "tests/db/test_schema.py::test_user_table"
    
  - id: "chk-002"
    item: "实现登录 API"
    checked: false
    depends_on:
      - "chk-001"
```

**关键特性**：
- **可回归**：已勾选项可因验证失败而回归
- **依赖传播**：被依赖项回归时，依赖项自动回归

---

## 6. 目录结构约定

### 6.1 文件组织

Issue Ticket 按类型和状态分层存储：

```
Issues/
├── Features/
│   ├── open/
│   │   └── FEAT-0123.md
│   ├── doing/
│   │   └── FEAT-0120.md
│   └── done/
│       └── FEAT-0100.md
├── Fixes/
│   ├── open/
│   └── done/
├── Chores/
│   └── ...
└── Archive/
    └── 2026-Q1/
        └── FEAT-0099.md
```

### 6.2 路径语义

- **文件存在 = 信号待处理**：Inbox 中有未处理的 Issue
- **文件移动 = 状态变更**：从 `open/` 移到 `doing/` 表示启动
- **Git 是档案**：历史记录在 Git 中，不在目录状态里

---

## 7. 设计原则

### 7.1 文件即状态

Issue 的状态由其文件系统位置决定，而非数据库记录：

```python
def get_status(issue_path: Path) -> str:
    """从路径推断状态"""
    return issue_path.parent.name  # 'open', 'doing', 'done'
```

### 7.2 可观测性优先

任何信息都应可直接通过文件系统访问：

```bash
# 查看所有进行中任务
ls Issues/Features/doing/

# 搜索包含特定标签的 Issue
grep -r "area:auth" Issues/

# 查看今日修改的 Issue
find Issues -name "*.md" -mtime 0
```

### 7.3 向前兼容

Schema 演进原则：
- 新增字段：向后兼容（旧文件无该字段）
- 废弃字段：保留解析，不报错
- 类型扩展：使用联合类型（`string | list`）

---

## 8. 结论

本文定义了 AHP 的记录系统：

1. **文本即记录**：Markdown + YAML 的本地文件格式，原生支持版本控制
2. **四阶段模型**：Draft → Doing → Review → Done 的协作生命周期
3. **丰富关联**：parent、dependencies、tags、wiki links 的多维关联
4. **可验证任务**：Stage 里程碑和 Checklist 的自动化验收

记录系统为智能体提供了结构化的工作上下文，是后续 Agent 集成和过程干预的基础载体。

---

## 参考

- [01. 问题定义与动机](./01_Motivation.md)
- [03. 智能体集成](./03_Agent_Integration.md)
