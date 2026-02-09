# 3.2 Agent Hooks：过程干预

## 摘要

Hooks 是在关键执行点插入的验证与干预机制。AHP 实现的 **ACL（Agent Control Language）**，基于社区通用的 Hooks 概念，扩展了 Issue 生命周期相关事件，实现智能体执行过程的干预控制。

---

## 1. 核心概念

### 1.1 什么是 Agent Hooks

Agent Hooks 是 AHP 实现的 ACL（Agent Control Language），是 AHP 控制协议的执行载体，提供：

- **时机选择**：在关键执行点插入干预
- **条件评估**：检查当前状态是否满足要求
- **信号生成**：根据评估结果产生干预信号
- **响应处理**：处理智能体的反馈

### 1.2 与 Git Hooks 的区别

| 特性 | Git Hooks | Agent Hooks |
|------|-----------|-------------|
| **触发时机** | Git 操作前后 | 智能体执行生命周期 |
| **干预对象** | Git 命令 | 智能体决策与工具调用 |
| **响应方式** | 退出码 | 信号强度（Block/Control/Prompt/Aid） |
| **上下文** | 有限的 Git 信息 | 完整的 Issue 与执行上下文 |

---

## 2. 触发器（Triggers）

### 2.1 触发点定义

触发器定义 Hook 的激活时机：

| 触发点 | 时机 | 典型用途 | 适用强度 |
|--------|------|----------|----------|
| `pre-issue-start` | Issue 启动前 | 依赖检查、环境准备 | block, control |
| `post-issue-start` | Issue 启动后 | 上下文加载、初始化 | aid |
| `pre-tool-use` | 工具调用前 | 权限验证、参数检查 | block, control |
| `post-tool-use` | 工具调用后 | 结果验证、日志记录 | aid |
| `pre-issue-submit` | Issue 提交前 | 验收检查、质量门禁 | block, control, prompt |
| `post-issue-submit` | Issue 提交后 | 审查触发、通知 | aid |
| `pre-issue-close` | Issue 关闭前 | 完成验证、归档检查 | block |
| `post-issue-close` | Issue 关闭后 | 复盘生成、度量记录 | aid |

### 2.2 触发器生命周期

```
Issue 生命周期：

pre-issue-start ──► post-issue-start ──► ...执行中... ──► pre-issue-submit ──► post-issue-submit ──► pre-issue-close ──► post-issue-close
       │                  │                                   │                    │                      │                    │
       ▼                  ▼                                   ▼                    ▼                      ▼                    ▼
   环境检查           上下文加载                          质量门禁            审查触发              完成验证            复盘生成
   依赖验证           初始化任务                          checklist           通知发送              归档检查            度量记录
```

### 2.3 触发条件

除了时机，还可以配置更细粒度的触发条件：

```yaml
hooks:
  pre-tool-use:
    # 仅对特定工具触发
    when:
      tool: ["Bash", "Write"]
    
  pre-issue-submit:
    # 基于 Issue 属性
    when:
      issue.type: "feature"
      files.changed_count: "> 10"
```

---

## 3. 预言机（Oracles）

### 3.1 预言机概述

预言机是 Hook 的决策组件，负责评估条件并返回干预信号：

```python
class Oracle(ABC):
    """预言机基类"""
    
    @abstractmethod
    def evaluate(self, context: HookContext) -> Signal:
        """
        评估条件，返回干预信号。
        
        Returns:
            Signal: 包含干预强度（block/control/prompt/aid）
        """
        pass
```

### 3.2 内置预言机

| 预言机 | 功能 | 默认强度 | 配置参数 |
|--------|------|----------|----------|
| `ChecklistValidator` | 检查 checklist 完成度 | block/prompt | `allow_partial`, `min_completion_rate` |
| `FileChangeLimiter` | 限制单次变更文件数 | control | `max_files`, `action` |
| `TestGate` | 要求测试通过 | block | `coverage_threshold`, `require_all_pass` |
| `SecurityScanner` | 扫描安全风险 | block/prompt | `rules`, `severity_threshold` |
| `DependencyChecker` | 检查依赖满足情况 | block | `manifest_files` |
| `LintChecker` | 代码风格检查 | prompt/control | `linters`, `auto_fix` |
| `CommitMessageValidator` | 提交信息验证 | prompt | `pattern`, `required_fields` |

### 3.3 预言机配置示例

```yaml
hooks:
  pre-issue-submit:
    # Checklist 验证
    - oracle: ChecklistValidator
      config:
        allow_partial: false           # 不允许部分完成
        min_completion_rate: 0.9       # 至少 90% 完成
        
    # 文件变更限制
    - oracle: FileChangeLimiter
      config:
        max_files: 20                  # 最多 20 个文件
        action: control                # 超出时自动控制
        control_action: split_batch    # 自动分批
        
    # 测试门禁
    - oracle: TestGate
      config:
        coverage_threshold: 80         # 覆盖率阈值
        require_all_pass: true         # 要求全部通过
```

### 3.4 自定义预言机

```python
class MyCustomOracle(Oracle):
    """自定义预言机示例：检查 API 文档完整性"""
    
    def __init__(self, config: dict):
        self.required_doc_files = config.get("required_files", [])
        self.intensity = config.get("intensity", "prompt")
    
    def evaluate(self, context: HookContext) -> Signal:
        # 获取变更的文件
        changed_files = context.issue.files.changed
        
        # 检查是否包含 API 变更
        api_files = [f for f in changed_files if "api" in f or "router" in f]
        
        if not api_files:
            return Signal.accept()  # 无 API 变更，通过
        
        # 检查文档是否更新
        doc_files = [f for f in changed_files if "docs" in f or "README" in f]
        missing_docs = []
        
        for api_file in api_files:
            expected_doc = self._get_expected_doc(api_file)
            if expected_doc not in doc_files:
                missing_docs.append(expected_doc)
        
        if missing_docs:
            if self.intensity == "block":
                return Signal.block(
                    reason=f"API 文档缺失: {missing_docs}",
                    resolution_path=[f"添加文档: {d}" for d in missing_docs]
                )
            else:
                return Signal.prompt(
                    message=f"检测到 API 变更，建议更新文档: {missing_docs}",
                    suggestions=["更新 API 文档", "确认无需更新"]
                )
        
        return Signal.accept()
```

---

## 4. 信号系统

### 4.1 信号强度

预言机评估后生成信号，强度分为四级：

| 强度 | 符号 | 强制性 | 智能体行为 |
|------|------|--------|-----------|
| **Block** | B | 强制 | 停止操作，根据 resolution_path 修复 |
| **Control** | C | 自动 | 接受参数调整，继续执行 |
| **Prompt** | P | 可选 | 阅读警告，可选择接受建议或继续 |
| **Aid** | A | 无 | 异步接收建议，不影响当前流程 |

### 4.2 信号结构

```typescript
interface Signal {
  header: {
    id: string;                    // UUID
    type: string;                  // 信号类型
    timestamp: string;             // ISO8601
    source: string;                // 预言机名称
    intensity: "block" | "control" | "prompt" | "aid";
    correlation_id?: string;       // 关联信号链
  };
  context: {
    hook: string;                  // 触发点
    issue_id: string;              // 关联 Issue
    files: string[];               // 相关文件
  };
  payload: {
    // Block
    reason?: string;
    resolvable?: boolean;
    resolution_path?: string[];
    
    // Control
    modifications?: Modification[];
    reversible?: boolean;
    
    // Prompt
    severity?: "low" | "medium" | "high";
    message?: string;
    suggestions?: string[];
    continue_allowed?: boolean;
    
    // Aid
    context_info?: string;
    best_practices?: string[];
    follow_ups?: string[];
  };
}
```

### 4.3 信号响应

智能体消费信号后返回响应：

```typescript
interface SignalResponse {
  signal_id: string;
  consumed_at: string;
  action: ConsumptionAction;
  details?: Record<string, any>;
}

type ConsumptionAction =
  // Block
  | "retry_after_fix"
  | "proceed_with_risk"
  | "abort"
  // Control
  | "accept_modification"
  | "reject_modification"
  // Prompt
  | "acknowledge"
  | "apply_suggestion"
  | "dismiss"
  // Aid
  | "suggestion_applied"
  | "suggestion_deferred";
```

---

## 5. Hook 配置

### 5.1 配置文件位置

```
~/.ahp/hooks.yaml              # 用户级默认
  ↓ (继承并覆盖)
./.ahp/hooks.yaml              # 项目级配置
  ↓ (继承并覆盖)
./.ahp/hooks.local.yaml        # 本地覆盖（gitignored）
```

### 5.2 配置格式

```yaml
# hooks.yaml 完整示例

hooks:
  # Issue 启动前
  pre-issue-start:
    - oracle: DependencyChecker
      config:
        manifest_files: ["package.json", "requirements.txt"]
      when:
        # 仅在特定条件下触发
        environment: ["development", "staging"]
        
  # Issue 启动后
  post-issue-start:
    - oracle: ContextLoader
      config:
        include_files: true
        include_git_history: true
        
  # 工具调用前
  pre-tool-use:
    - oracle: PermissionChecker
      config:
        dangerous_commands: ["rm -rf", "DROP TABLE"]
        require_confirmation: true
      when:
        tool: ["Bash", "Database"]
        
  # 工具调用后
  post-tool-use:
    - oracle: ChangeLogger
      config:
        log_level: "info"
      when:
        tool: ["Write", "Edit", "Delete"]
        
  # Issue 提交前 - 质量门禁
  pre-issue-submit:
    # 1. Checklist 验证
    - oracle: ChecklistValidator
      config:
        allow_partial: false
      priority: 1  # 优先执行
      
    # 2. 文件变更限制
    - oracle: FileChangeLimiter
      config:
        max_files: 20
        action: prompt
      priority: 2
      
    # 3. 测试门禁
    - oracle: TestGate
      config:
        coverage_threshold: 80
        require_all_pass: true
      priority: 3
      
    # 4. 安全扫描
    - oracle: SecurityScanner
      config:
        rules: ["no-secrets", "no-sql-injection"]
      priority: 4
      
  # Issue 提交后
  post-issue-submit:
    - oracle: ReviewTrigger
      config:
        notify_reviewers: true
        create_pr: true
        
  # Issue 关闭前
  pre-issue-close:
    - oracle: CompletionVerifier
      config:
        require_tests: true
        require_docs: true
        
  # Issue 关闭后
  post-issue-close:
    - oracle: RetrospectiveGenerator
      config:
        generate_metrics: true
        archive_issue: true
```

### 5.3 配置选项

| 选项 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `oracle` | string | 预言机名称 | 必填 |
| `config` | object | 预言机配置 | `{}` |
| `when` | object | 触发条件 | `{}`（总是触发） |
| `priority` | number | 执行优先级 | 0（并行执行） |
| `enabled` | boolean | 是否启用 | `true` |
| `async` | boolean | 异步执行 | `false` |

---

## 6. 执行流程

### 6.1 Hook 执行时序

```
智能体发起操作
      │
      ▼
┌─────────────┐
│ Hook 触发   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 条件过滤    │  <-- when 条件检查
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 预言机评估   │  <-- 按 priority 顺序执行
│ - 条件检查   │
│ - 强度确定   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 信号生成    │
│ - 构造载荷   │
│ - 添加上下文 │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│ 信号传递    │────►│ 智能体消费  │
└─────────────┘     └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ 响应处理    │
                    │ - 允许继续  │
                    │ - 要求修复  │
                    │ - 参数调整  │
                    └─────────────┘
```

### 6.2 信号处理示例

```python
# 智能体尝试提交
agent.submit_issue("FEAT-0123")

# pre-issue-submit hook 触发
signal = oracle.evaluate(context)

# Case 1: Block
if signal.intensity == "block":
    agent.receive_message("提交被拒绝：checklist 未完成")
    agent.fix_issues(signal.resolution_path)
    
# Case 2: Control  
elif signal.intensity == "control":
    agent.receive_message("batch_size 已从 1000 调整为 100")
    agent.accept_modification(signal.modifications)
    
# Case 3: Prompt
elif signal.intensity == "prompt":
    agent.receive_message("警告：单次修改超过 20 个文件，建议分步提交")
    choice = agent.decide("继续" | "分步")
```

---

## 7. 设计原则

### 7.1 渐进干预

优先使用低级别控制，必要时升级：

```
首次提交（Prompt）──► 未修复（Control）──► 仍违规（Block）
     ▲                                            │
     └──────────── 修复后继续 ─────────────────────┘
```

### 7.2 上下文敏感

同一规则在不同上下文产生不同强度的信号：

```python
def evaluate_change_size(context: Context) -> Signal:
    changed = len(context.files.changed)
    
    # 上下文敏感：根据环境调整阈值
    if context.environment == "production":
        threshold = 10
        intensity = "block" if changed > threshold else "allow"
    else:
        threshold = 30
        intensity = "prompt" if changed > threshold else "allow"
    
    return Signal(intensity=intensity, ...)
```

### 7.3 反馈闭环

干预历史用于优化策略：

```
[干预执行] ──► [效果记录] ──► [策略分析] ──► [规则调整]
     │              │              │
     └──────────────┴──────────────┘
        （信号日志支持持续改进）
```

---

## 8. 完整示例

### 场景：Issue 提交

**背景**：智能体完成 FEAT-0123，执行 `monoco issue submit`

**执行过程**：

```
1. pre-issue-submit hook 触发
   │
   ├─► checklist-validator
   │   发现 2/3 项未完成
   │   → 生成 block 信号
   │
   └─► 智能体接收信号
       "提交被拒绝：checklist 未完成 [chk-003]"
       修复建议："完成 API 文档"

2. 智能体修复后再次提交
   │
   ├─► checklist-validator
   │   全部完成 → 通过
   │
   ├─► change-size-limiter
   │   发现 25 个文件变更
   │   → 生成 prompt 信号
   │
   └─► 智能体接收信号
       "警告：大变更（25 文件），建议分步？"
       选择："继续"（确认可接受）

3. pre-issue-submit 通过
   → Issue 进入 review 状态
   → post-issue-submit hook 触发
      → 生成 aid 信号
      → "已通知审查者，预计 2 小时响应"
```

**信号日志**：

```jsonl
{"timestamp": "2026-02-09T10:00:00Z", "hook": "pre-issue-submit", "intensity": "block", "source": "checklist-validator", "consumed": true, "action": "retry_after_fix"}
{"timestamp": "2026-02-09T10:15:00Z", "hook": "pre-issue-submit", "intensity": "prompt", "source": "change-size-limiter", "consumed": true, "action": "acknowledge"}
{"timestamp": "2026-02-09T10:15:01Z", "hook": "post-issue-submit", "intensity": "aid", "source": "notification", "consumed": true, "action": "suggestion_applied"}
```

---

## 参考

- [3.1 AGENTS.md](./01_AGENTS_md.md)
- [3.3 Agent Skills](./03_Agent_Skills.md)
- [04. 控制协议](../04_Control_Protocol.md)
