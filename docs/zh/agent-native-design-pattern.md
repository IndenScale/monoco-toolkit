# Agent Native Software Design Patterns

## 代理原生软件设计模式

> **Design for Agents first, Humans second.** > **设计优先服务于代理，其次才是人类。**

Agent Native 软件与传统软件有着本质的区别。传统软件假定用户具有直觉和纠错能力，而 Agent Native 软件必须假定用户（代理）需要确定性、显式性和幂等性。

## 1. CLI First Principle (CLI 优先原则)

CLI 是 Agent 最自然的交互界面。

- **Programmable Output**: 必须提供关闭 Rich Print/ANSI Color 的选项（通常通过 `--json` 或自动检测非 TTY 环境）。
- **Parsable Structure**: stdout 仅输出结构化数据（JSON），stderr 用于日志和诊断信息。严禁在 stdout 中混合通过 print 输出调试日志。

## 2. Explicit over Implicit (显式优于隐式)

Agent 在处理“上下文”和“隐含状态”时容易出错。

- **Verbose Parameters**: 拥抱冗长的参数列表，而不是依赖隐含的配置文件查找顺序。
  - _Bad_: `monoco build` (依赖当前目录猜测目标)
  - _Good_: `monoco build --target ./src/main.py --out ./dist`
- **State Transparency**: 如果命令依赖某种状态，必须在错误信息中明确指出缺失的状态文件路径。

## 3. Zero Interaction (零交互)

交互式输入（Interactive Prompt, Wizard）是 Agent 自动化的噩梦。

- **Avoid Prompts**: 所有的输入都必须可以通过参数（Arguments/Options）提供。
- **No "Are you sure?"**: 如果需要确认，必须支持 `--yes` 或 `--force` 标志。
- **Dry Run**: 对于破坏性操作，提供 `--dry-run` 选项让 Agent 预演结果。

## 4. Declarative & Idempotent (声明式与幂等性)

Agent 可能会重复执行命令，或者在任务中途失败重试。

- **Idempotency**: 多次运行相同的命令应该产生相同的结果，且不会报错（或返回安全的状态码）。
  - `create --id 123` 如果已存在，不应 Crash，而应返回 "Already Exists" 或执行 "Upsert"（取决于语义）。
- **Happy Path APIs**: 提供高级的、聚合的 API 覆盖常见路径 (`create_feature` 而不是 `create_file` + `write_metadata`)。
- **Safety Rails**: 除非使用 `--force`，否则不应覆盖已存在且内容冲突的文件。

## 5. File as API & Governance (文件即 API 与治理)

允许 Agent 直接操作底层数据（文件），而不是强迫其必须通过 CLI 交互。但必须提供治理手段。

- **Hackability**: 允许用户（或 Agent）直接用编辑器修改 `.md` 或 configuration 文件。不要设计二进制或不透明的存储格式。
- **Trust but Verify (Lint/Check)**:
  - 必须提供 `lint` 或 `check` 命令。
  - 在关键路径（如 git commit, build）挂载检查钩子。
  - 如果 Agent 手动修改文件破坏了 Schema，`lint` 命令必须能给出精确的修复建议（如：`Line 5: Missing 'status' field`）。
