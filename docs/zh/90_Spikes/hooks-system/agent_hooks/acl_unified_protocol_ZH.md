# 领域防腐层 (ACL) 设计：统一 Agent Hooks 协议

> 关联 Issue: [FEAT-0173](../../../Issues/Features/open/FEAT-0173-implement-universal-hooks-registration-and-install.md)

## 1. 核心问题

Claude Code 和 Gemini CLI 的 Hooks 机制虽然理念一致（JSON via stdin/stdout），但在细节上存在细微碎片化：

- **字段差异**：Claude 使用 `permissionDecision`，Gemini 使用 `decision`。
- **事件命名**：Claude 的 `PreToolUse` 对标 Gemini 的 `BeforeTool`。
- **环境上下文**：环境变量名前缀不同（`CLAUDE_` vs `GEMINI_`）。

如果我们直接编写针对特定 Agent 的脚本，会导致逻辑碎片化。我们需要构建一个 **防腐层 (Anti-Corruption Layer)**，让用户编写一次 Hook，即可在多个 Agent 中运行。

## 2. 统一协议定义 (Monoco Hook Protocol)

Monoco 定义一套中立的输入/输出模型，作为防腐层的“核心协议”。

### 2.1 统一事件映射 (Event Mapping)

| Monoco 事件 (Agnostic) | Claude Code        | Gemini CLI     | Git (Native)  | VS Code (IDE)  |
| :--------------------- | :----------------- | :------------- | :------------ | :------------- |
| `ON_SESSION_START`     | `SessionStart`     | `SessionStart` | -             | `onFolderOpen` |
| `ON_BEFORE_TOOL`       | `PreToolUse`       | `BeforeTool`   | -             | -              |
| `ON_BEFORE_COMMIT`     | -                  | -              | `pre-commit`  | `onWillSave`   |
| `ON_AFTER_COMMIT`      | -                  | -              | `post-commit` | -              |
| `ON_BEFORE_AGENT`      | `UserPromptSubmit` | `BeforeAgent`  | -             | -              |
| `ON_AFTER_AGENT`       | `Stop`             | `AfterAgent`   | -             | -              |
| `ON_FILE_CHANGE`       | -                  | -              | -             | `onSave`       |

### 2.2 统一决策模型 (Decision Model)

Monoco 内部统一使用 `decision` 字段，并由适配器负责翻译：

```json
{
  "decision": "allow | deny | ask",
  "reason": "...",
  "message": "...",
  "metadata": {}
}
```

## 3. 防腐层实现策略

### 3.1 注入式适配器 (Injected Adapter Strategy)

当 `monoco sync` 时，它将充当 **配置编译器 (Configuration Compiler)**，将 Monoco 的通用 Hook 声明转化为 Agent 特定的配置逻辑：

1. **自动配置注入**：扫描 Toolkit 功能库中的 Hooks，根据元数据自动更新：
   - `.claude/settings.json` 的 `hooks` 数组。
   - `.gemini/settings.json` 的 `hooks` 数组。
2. **中继执行 (Choreography)**：注入的配置中，`command` 字段将指向 Monoco 提供的 **通用运行时拦截器 (Universal Runtime Interceptor)**。
3. **适配器映射 (Mapping)**：在拦截器内部，领域适配器逻辑，根据当前运行环境（由拦截器探测）完成输入/输出的透明转换。

### 3.2 运行时拦截器与其适配逻辑 (Runtime Interceptor & Adapters)

Monoco 提供的 `monoco-hook-interceptor` (Python/Shell 实现) 将内置多平台适配能力：

```python
#### 拦截器伪代码实例
class UniversalInterceptor:
    def run(self, hook_script_path):
        raw_input = sys.stdin.read()

        #### 1. 自动识别平台
        adapter = self.detect_adapter() # ClaudeAdapter or GeminiAdapter

        #### 2. 输入对齐
        universal_input = adapter.translate_input(raw_input)

        #### 3. 执行真实业务脚本
        #### 将统一后的输入传给用户的原始脚本
        process = subprocess.Popen([hook_script_path], stdin=PIPE, stdout=PIPE)
        universal_output = process.communicate(input=universal_input)

        #### 4. 输出回译为平台协议
        final_json = adapter.translate_output(universal_output)
        print(json.dumps(final_json))
```

## 4. 优势

1. **DRY (Don't Repeat Yourself)**：编写一次安全扫描脚本，同时保护所有 Agent。
2. **平滑演进**：如果未来出现了新的 Agent (如 GPT-CLI)，只需添加一个新的 Adapter，无需修改现有脚本。
3. **强制策略**：Monoco 可以在 ACL 层强制执行安全策略（如：禁止所有 Agent 执行 `rm -rf`），而无需在每个 Hook 脚本里写重复代码。

## 5. 结论

直接构建防腐层是 **FEAT-0173** 的核心价值所在。我们将不再仅仅是“分发文件”，而是提供一个 **“Agent 钩子运行时适配环境”**。
