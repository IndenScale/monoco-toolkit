# Gemini CLI Hooks 调查报告

> 本文档详细介绍了 Gemini CLI 的 Hooks 系统机制，包括生命周期、配置方式、通信协议及安全性设计。作为 Monoco 通用 Hooks 机制（FEAT-0173）的重要参考。

## 1. 核心理念

Gemini CLI 的 Hooks 是在代理循环（Agentic Loop）特定点触发的脚本或程序。它们允许开发者在不修改 CLI 源码的情况下拦截、定制和增强 Agent 的行为。

- **同步执行**：Hooks 运行在 Agent 循环中，CLI 会等待所有匹配的 Hooks 执行完毕后再继续。
- **解耦设计**：基于标准 I/O（stdin/stdout）和 JSON 进行通信，支持任何编程语言。

## 2. 生命周期与事件 (Events)

Gemini CLI 定义了贯穿整个会话生命周期的事件：

| 事件                    | 触发时机                        | 常见用途                                        |
| :---------------------- | :------------------------------ | :---------------------------------------------- |
| **SessionStart**        | 会话开始/恢复/清空时            | 加载初始上下文、设置环境变量、初始化资源。      |
| **SessionEnd**          | 会话结束（退出/清空）时         | 清理临时文件、保存状态、发送遥测数据。          |
| **BeforeAgent**         | 用户提交 Prompt 后，规划开始前  | 注入动态上下文、验证 Prompt 合法性、拦截 Turn。 |
| **AfterAgent**          | 每轮 Turn 结束，生成最终响应后  | 验证响应质量、触发自动重试（Retry）。           |
| **BeforeModel**         | 请求发送给 LLM 之前             | 劫持/重写提示词、更换模型、模拟响应（Mock）。   |
| **AfterModel**          | 接收到 LLM 响应（或流式分片）后 | 实时敏感词过滤（PII Redaction）、交互记录。     |
| **BeforeToolSelection** | LLM 决定使用哪些工具前          | 限制可用工具范围（Tool Filtering）。            |
| **BeforeTool**          | 工具实际执行前                  | 参数校验、安全检查、参数重写（Rewrite）。       |
| **AfterTool**           | 工具执行完成后                  | 结果审计、隐藏敏感结果、注入额外反馈上下文。    |
| **PreCompress**         | 上下文压缩前（异步）            | 状态导出、用户通知。                            |
| **Notification**        | 系统发出通知（如权限请求）时    | 第三方通知推送、日志记录。                      |

## 3. 通信协议 (Protocol)

### 3.1 黄金准则：JSON 纯净度

- **stdout**：必须**仅**输出最终的 JSON 对象。任何多余的 `echo` 或打印都会导致解析失败。
- **stderr**：用于所有调试日志和异常反馈。CLI 捕获 `stderr` 但不会解析为 JSON。

### 3.2 退出代码 (Exit Codes)

| 退出代码             | 含义     | 行为影响                                                                      |
| :------------------- | :------- | :---------------------------------------------------------------------------- |
| **0 (Success)**      | 成功     | 解析 stdout 为 JSON。这是处理逻辑（包括拒绝操作）的首选方式。                 |
| **2 (System Block)** | 紧急制动 | 立即阻塞当前操作（工具、Turn 等）。使用 stderr 内容作为拒绝理由反馈给 Agent。 |
| **其他**             | 警告     | 非致命错误。CLI 显示警告但仍按原始参数继续执行。                              |

### 3.3 输入/输出 Schema

- **输入 (stdin)**：包含 `session_id`, `cwd`, `hook_event_name`, `timestamp` 以及特定事件数据（如 `tool_input`, `prompt`）。
- **输出 (stdout)**：
  - `decision`: `"allow"` 或 `"deny"` (等同于 `"block"`)。
  - `reason`: 当被拒绝时的说明文字。
  - `systemMessage`: 直接显示给用户的即时消息。
  - `continue`: (`boolean`) 若为 `false`，则立即停止整个 Agent 循环。
  - `hookSpecificOutput`: 用于特定事件的增强控制（如 `tool_input` 重写、`additionalContext` 注入）。

## 4. 匹配器机制 (Matchers)

Hooks 通过 `matcher` 字段定义触发条件：

- **工具事件**：使用**正则表达式**（如 `"write_.*"`, `"mcp__.*"`）。
- **生命周期事件**：使用**精确字符串**（如 `"startup"`, `"exit"`）。
- **通配符**：`"*"` 匹配该事件的所有发生。

## 5. 配置层级 (Configuration)

支持多层级配置合并（优先级从高到低）：

1. **项目级**：`.gemini/settings.json`（随代码库分发）。
2. **用户级**：`~/.gemini/settings.json`（全局偏好）。
3. **系统级**：`/etc/gemini-cli/settings.json`（企业策略）。
4. **扩展级**：已安装的扩展插件自带的 Hooks。

## 6. 安全性设计 (Security)

Gemini CLI 对 Hooks 采取了严密的防御措施：

- **指纹识别 (Fingerprinting)**：CLI 会记录项目 Hook 的 `name` 和 `command` 指纹。
- **首次确认**：发现新指纹或指纹变更（如 `git pull` 后脚本改变）时，会强制警告用户并要求审核。
- **环境变量脱敏**：默认可以开启环境变量过滤，防止脚本意外访问或泄露 `GEMINI_API_KEY` 等敏感信息。

## 7. 与 Claude Code 的对比总结

| 特性           | Claude Code Hooks             | Gemini CLI Hooks                  |
| :------------- | :---------------------------- | :-------------------------------- |
| **核心协议**   | JSON via stdin/stdout         | JSON via stdin/stdout             |
| **阻塞机制**   | `permissionDecision: "deny"`  | `decision: "deny"` 或 Exit Code 2 |
| **Hook 类型**  | Command, Prompt, Agent        | Command (目前)                    |
| **异步支持**   | 支持 (async: true)            | 仅部分系统事件支持                |
| **环境注入**   | 支持 `CLAUDE_ENV_FILE` 持久化 | 支持 `GEMINI_ENV_FILE` (别名兼容) |
| **安全模型**   | Snapshot 机制 + 完整性核验    | Fingerprint 机制 + 变更警告       |
| **跨项目共享** | 插件 (Plugins) / Skills       | 扩展 (Extensions)                 |

## 8. 调研结论：对 Monoco 的启示

1. **元数据标准化**：Monoco 应采用类似的 Front Matter 声明方式（FEAT-0173 确定的方向），支持 `type`, `matcher`, `priority` 等元数据。
2. **通信模型对齐**：Monoco 的 `UniversalHookManager` 应当优先支持标准 I/O JSON 协议，以便无缝集成现有 Agent 生态的脚本。
3. **分层管理**：需要支持 `.monoco/` 项目级、用户全局级以及从 Features/Skills 中动态注入的 Hooks。
4. **决策分发器 (Dispatcher)**：`monoco sync` 应当能够将同一个 Hook 根据其 Front Matter 自动分发到不同的目标（如同时安装到 `.git/hooks`, `.claude/hooks` 和 `.gemini/hooks`）。
