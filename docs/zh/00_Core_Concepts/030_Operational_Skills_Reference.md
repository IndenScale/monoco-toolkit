# 标准操作程序 (SOP) 与技能规范

## 1. 生命周期管理技能 (Lifecycle Skills)

Monoco 定义了严格的 Issue 生命周期流转标准，Agent 必须遵循以下操作序列：

### 1.1 标准工作流
1.  **创建 (Create)**: 使用 `monoco issue create`。必须准确选择类型 (Feature/Fix/Chore) 并提供语义清晰的标题。
2.  **启动 (Start)**: 使用 `monoco issue start <ID>`。此命令会自动创建并切换至对应的 Git 分支 (e.g., `feat/feature-name`)，并建立隔离的开发环境。
3.  **实现 (Implement)**: 依照 Issue 描述进行编码。
4.  **验证 (Verify)**: 运行测试与 Linter。
5.  **提交 (Submit)**: 使用 `monoco issue submit <ID>`。此操作将状态流转至 `review`，并触发 CI 检查。
6.  **关闭 (Close)**: 使用 `monoco issue close <ID>`。此为原子化操作，包含代码合并、分支删除、环境清理与 Issue 归档。

## 2. 上下文维护技能 (Context Maintenance)

为维持系统的可校验性，Agent 必须主动维护上下文的一致性。

### 2.1 文件同步 (`sync-files`)
*   **指令**: `monoco issue sync-files`
*   **原理**: 该命令对比当前分支 HEAD 与基准分支 (Base Branch) 的差异。
*   **作用**: 自动将所有变更文件的路径追加至 Issue 的 `files` 字段。
*   **时机**:
    *   在引入新文件后。
    *   在收到 Hooks 的 `ScopeViolation` 警告后。
    *   在执行 `submit` 之前 (强制要求)。

### 2.2 自我诊断 (`lint`)
*   **指令**: `monoco issue lint`
*   **作用**: 触发静态分析引擎对当前 Issue 文件进行全量扫描。
*   **时机**: 在手动修改了 Issue 描述或元数据后，必须运行此命令以确保格式合规。

## 3. 外部知识集成 (Knowledge Integration)

Monoco 严禁 Agent 直接从互联网复制不可溯源的代码片段。所有外部参考必须纳入 Spike 系统管理。

### 3.1 Spike 机制
*   **指令**: `monoco spike add <URL>`
*   **原理**: 将远程 Git 仓库克隆至 `.references/` 目录，并将其视为**只读卷 (Read-only Volume)**。
*   **作用**:
    *   构建隔离的知识上下文，避免污染项目源码。
    *   确保引用的外部代码具有确定的版本号 (Git Commit Hash)。
*   **规范**: Agent 在需要参考外部实现时，应先执行 Spike 操作，通过阅读 `.references/` 下的源码来获取知识，而非凭空臆造。
