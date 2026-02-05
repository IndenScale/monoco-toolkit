# Issue 生命周期 (The Issue Lifecycle)

Monoco 的 Issue 系统采用独特的**双层状态机 (Two-Layer State Machine)** 设计，解耦了文件的**物理存储位置**与任务的**逻辑流转阶段**。

## 1. 双层状态模型

### 1.1 Status (物理状态)
**Status** 决定了 Issue 文件在文件系统中的**物理路径**。它的设计原则是：**保持目录树的整洁**。

| Status | 目录路径 | 含义 |
| :--- | :--- | :--- |
| `open` | `Issues/{Type}/open/` | 活跃任务。当前正在进行或排队中的工作。 |
| `closed` | `Issues/{Type}/closed/` | 归档任务。已完成或已废弃的历史记录。 |
| `backlog` | `Issues/{Type}/backlog/` | 待办池。未来可能做，但当前不关注的任务。 |

这种设计的优势在于，Agent 或开发者只需要关注 `open` 目录，就能获得当前的关注点（Focus），而不会被大量的历史文件干扰。

### 1.2 Stage (逻辑状态)
**Stage** 描述了任务在工作流中的**精确进度**。它存储在 Issue 的 Front Matter 元数据中。

```yaml
---
status: open
stage: doing  # <--- 逻辑状态
---
```

Stage 的流转触发不同的治理规则：

1.  **Draft (草案)**:
    - 初始状态。
    - **允许**: 随意修改。
    - **禁止**: `monoco issue start` (必须先评审通过)。
2.  **Ready (就绪)**:
    - 已完成需求评审。
    - **等待**: 分配给 Agent 或工程师。
3.  **Doing (进行中)**:
    - 正在开发。
    - **触发**: 创建 Feature Branch。
    - **Hook**: 每次代码提交时自动记录 Touched Files。
4.  **Review (评审)**:
    - 开发完成，发起 PR。
    - **阻塞**: CI 测试必须通过，Linter 必须通过。
5.  **Done (完成)**:
    - 代码已合并入 Trunk。
    - **物理迁移**: 文件移动到 `closed` 目录。
6.  **Freezed (冻结)**:
    - 任务暂停或挂起。

## 2. 状态流转矩阵

Monoco 通过 `monoco issue` CLI 命令驱动状态流转，同时保证 Status 和 Stage 的一致性。

| 动作 | 命令 | Status 变化 | Stage 变化 | 副作用 (Side Effects) |
| :--- | :--- | :--- | :--- | :--- |
| **创建** | `create` | `-> open` | `-> draft` | 生成文件 |
| **开始** | `start` | `open` | `ready -> doing` | 创建/切换 Git 分支 |
| **提交** | `submit` | `open` | `doing -> review` | 发起 Review, 运行 CI |
| **拒绝** | `reject` | `open` | `review -> doing` | 附带评审意见 |
| **完成** | `close` | `open -> closed` | `review -> done` | 合并分支, 删除分支, 移动文件 |
| **搁置** | `shelve` | `open -> backlog` | `* -> freezed` | 移动文件 |

## 3. 为什么需要双层设计？

如果只用一个 `status` 字段（如 Jira）：
- 所有的 Ticket 都在同一个列表里，难以区分“正在做”和“待办”。
- 如果用文件夹区分所有状态（`Issues/draft/`, `Issues/doing/`, ...），文件移动过于频繁，Git Log 会变得混乱，且难以追踪文件历史。

Monoco 的折中方案：
- **低频移动**: 只有在开始 (`backlog -> open`) 和结束 (`open -> closed`) 时才发生文件移动。
- **高频修改**: 开发过程中的状态变化 (`doing <-> review`) 只修改文件内的 Metadata，不产生文件移动，保持 Git History 清晰。
