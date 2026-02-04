# IDE Hooks 标准化方案 (VS Code & LSP)

> 关联 Issue: [FEAT-0173](../../../Issues/Features/open/FEAT-0173-implement-universal-hooks-registration-and-install.md)

## 1. 核心目标

IDE Hooks 旨在将 Monoco 的工具能力无缝集成到开发者的日常编写流中。IDE 本身没有原生类似 Git 的 Hook 机制，因此 Monoco 通过模拟和配置注入的方式实现：

- **零配置感知**：在打开项目时自动加载环境。
- **保存即反馈**：在文件保存时触发校验或格式化。
- **协议级整合**：通过 LSP (Language Server Protocol) 或 MCP (Model Context Protocol) 实现实时的状态钩子。

## 2. 机制与实现路径

我们将 IDE Hooks 分为三个等级的实现：

### 2.1 等级一：配置注入 (Configuration Injection) - 无插件依赖

这是 Monoco 目前推荐的基础模式，通过 `monoco sync` 修改 `.vscode/` 目录：

| 类型              | 触发点 (Event) | VS Code 实现方式                                      |
| :---------------- | :------------- | :---------------------------------------------------- |
| `ON_PROJECT_OPEN` | 启动项目       | `.vscode/tasks.json` 中 `runOn: folderOpen` 的任务    |
| `ON_FILE_SAVE`    | 文件保存       | `.vscode/settings.json` 的 `editor.codeActionsOnSave` |
| `ON_TASK_RUN`     | 自定义任务     | `.vscode/tasks.json` 中的自定义脚本调用               |

### 2.2 等级二：协议代理 (Protocol-based) - 跨编辑器

利用 LSP/MCP 实现动态钩子：

- **MCP 触发器**: 当 LLM 通过 MCP 访问上下文时，Monoco 作为服务器可以触发 `ON_BEFORE_CONTEXT_READ` 钩子。
- **LSP 诊断**: 将 Monoco Issue 的检查结果（Linter）实时反馈在编辑器的横波浪线下。

### 2.3 等级三：Monoco VSCode Extension - 深度集成

开发官方插件，通过 IDE API 监听以下事件：

- `onDidChangeTextDocument`: 实时代码感知。
- `onDidCreateFiles / onDeleteFiles`: 文件生命周期钩子。

## 3. 协议定义 (Front Matter)

```bash
#!/bin/bash
# ---
# type: ide
# ide_type: vscode
# event: onSave
# matcher: "src/**/*.ts"
# description: 保存时自动执行类型检查
# ---

# Hook logic...
npm run type-check -- --files $CURRENT_FILE
```

## 4. 自动化分发逻辑

当 `monoco sync` 运行阶段，`UniversalHookManager` 将执行以下动作：

1. **Task 聚类**: 收集所有 `event: onOpen` 的 Hooks，并在 `.vscode/tasks.json` 中创建一个复合任务 (Compound Task) 并在启动时运行。
2. **Action 自动化**:
   - 对于 `onSave` 钩子，将其转化为一个项目级的 `task`。
   - 然后在 `settings.json` 中配置 `editor.codeActionsOnSave` 执行该任务的 alias。
3. **环境对齐**: 确保所有 IDE 任务都携带正确的环境变量（如 `MONOCO_PROJECT_ROOT`）。

## 5. IDE 钩子的约束

- **非阻塞性**: IDE 钩子（尤其是 `onSave`）必须在 200ms 内响应或异步运行，以免阻塞编辑器 UI。
- **幂等性**: 频繁触发的情况下不能导致资源泄漏。
- **静默失败**: 如果 Hook 失败，不应干扰正常的代码编辑，应通过通知栏或输出日志报错。

## 6. 统一生态的协同

**场景示例：**

1. 开发者在 VS Code 中保存了一个文件（触发 **IDE Hook**）。
2. 该 Hook 发现代码违反了当前 Feature 的架构设计。
3. 它不仅在 IDE 报错，还向 Monoco 的 **Mailroom** 发送了一个 Event。
4. 下次开发者启动 Agent 时，Agent 通过 **Agent Hook (SessionStart)** 立即感知到该违规操作并由于 ACL 防腐层逻辑主动询问。
