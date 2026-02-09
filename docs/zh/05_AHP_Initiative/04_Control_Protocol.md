# 04. 控制协议

## 摘要

控制协议定义 AHP 的干预机制。通过连续控制光谱确定干预强度，通过信号系统实现干预通信，Hooks 作为集成点将控制逻辑嵌入智能体执行流程。

---

## 1. 协议概述

### 1.1 为什么需要控制协议

智能体执行是开放的生成过程，需要机制在关键节点进行引导而非仅依赖事后验证。控制协议提供：

- **强度分级**：从建议到阻止的连续干预空间
- **时机选择**：在关键执行点插入干预
- **双向通信**：智能体与 AHP 的信息交换格式

### 1.2 协议栈

```
┌─────────────────────────────────────────────────────┐
│  Agent Layer (LLM + Tools)                          │
├─────────────────────────────────────────────────────┤
│  Integration Layer (Hooks)                          │
│  - 触发器（时机选择）                                  │
│  - 预言机（条件评估）                                  │
├─────────────────────────────────────────────────────┤
│  Signal Layer (通信格式)                             │
│  - 信号头（元数据）                                   │
│  - 载荷（干预细节）                                   │
├─────────────────────────────────────────────────────┤
│  Control Layer (强度分级)                            │
│  - Block / Control / Prompt / Aid                   │
├─────────────────────────────────────────────────────┤
│  Record Layer (Issue Tickets)                       │
└─────────────────────────────────────────────────────┘
```

---

## 2. 连续控制光谱

### 2.1 四级干预模型

控制光谱定义从"阻止"到"赋能"的四个干预级别：

| 级别 | 符号 | 强制性 | 时机 | 核心操作 |
|------|------|--------|------|----------|
| **Blocking** | B | 高 | pre-event | 拒绝执行 |
| **Controlling** | C | 中 | pre-event | 参数调整 |
| **Prompting** | P | 低 | pre-event | 风险提醒 |
| **Aiding** | A | 无 | post-event | 建议/复盘 |

偏序关系：$B \prec C \prec P \prec A$（强制性递减）

### 2.2 级别语义

#### Blocking（阻止级）

```
IF condition THEN deny_execution
```

**适用场景**：
- 数据丢失风险（不可逆操作）
- 安全合规违规
- 前置条件不满足

**决策结构**：

```json
{
  "level": "blocking",
  "decision": "deny",
  "reason": "Checklist 未完成: [chk-001, chk-002]",
  "resolvable": true,
  "resolution_path": [
    "完成 chk-001: 设计数据库 Schema",
    "完成 chk-002: 实现登录 API"
  ]
}
```

#### Controlling（控制级）

```
allow_execution WITH modification
```

**适用场景**：
- 性能影响可控（自动分批）
- 自动修复可行（参数优化）
- 安全降级可接受（沙箱限制）

**决策结构**：

```json
{
  "level": "controlling",
  "decision": "allow_with_modification",
  "modifications": [
    {
      "target": "batch_size",
      "original": 10000,
      "updated": 1000,
      "reason": "避免内存溢出"
    }
  ],
  "reversible": true
}
```

#### Prompting（提示级）

```
allow_execution WITH warning
```

**适用场景**：
- 风险存在但可接受
- 复杂度警告（大变更）
- 依赖提示（影响分析）

**决策结构**：

```json
{
  "level": "prompting",
  "decision": "warn",
  "severity": "medium",
  "message": "单次修改涉及 25 个文件，建议分步提交",
  "suggestions": [
    "拆分为 3 个独立提交",
    "先提交核心变更，再提交测试"
  ],
  "continue_allowed": true
}
```

#### Aiding（赋能级）

```
execution_done THEN suggest
```

**适用场景**：
- 最佳实践分享
- 知识沉淀
- 自动化后续

**决策结构**：

```json
{
  "level": "aiding",
  "decision": "suggest",
  "context": "提交完成: 5 文件修改，新增 200 行",
  "suggestions": [
    {
      "type": "best_practice",
      "description": "建议检查测试覆盖率"
    },
    {
      "type": "follow_up",
      "description": "自动创建文档更新任务"
    }
  ]
}
```

### 2.3 级别选择决策树

```
识别风险点
    │
    ▼
风险是否可接受？
    │
    ├──────[否]──────► 能否自动修复？
    │                    ├──[否]──► Blocking
    │                    └──[是]──► Controlling
    │
    ├──────[是]──────► 需提醒？
    │                    ├──[是]──► Prompting
    │                    └──[否]──► 正常执行
    │
    └──────[事后]─────► 建议有用？
                         ├──[是]──► Aiding
                         └──[否]──► 无干预
```

---

## 3. 信号系统

### 3.1 信号定义

信号是 AHP 的基本通信单元，在干预点传递控制信息：

```typescript
interface Signal {
  header: SignalHeader;
  context: SignalContext;
  payload: SignalPayload;
}

interface SignalHeader {
  id: string;              // UUID
  type: string;            // 信号类型
  timestamp: string;       // ISO8601
  source: string;          // 来源组件
  intensity: "block" | "control" | "prompt" | "aid";
  correlation_id?: string; // 关联信号链
}
```

### 3.2 信号类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **生命周期** | 智能体执行事件 | `session-start`, `task-complete` |
| **领域** | Issue 管理事件 | `pre-issue-start`, `post-issue-submit` |
| **策略** | 规则触发 | `security-violation`, `quality-threshold` |

### 3.3 信号强度与消费方式

| 强度 | 消费要求 | 响应时间 | 可忽略 |
|------|----------|----------|--------|
| `block` | 强制响应 | 同步 | 否 |
| `control` | 自动应用 | 同步 | 否（透明） |
| `prompt` | 可选响应 | 同步/异步 | 是 |
| `aid` | 异步消费 | 异步 | 是 |

### 3.4 信号响应

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

## 4. 与 Hooks 的集成

### 4.1 Hook 作为集成点

Hooks 是控制协议的执行载体，在特定触发点：
1. 评估条件（预言机）
2. 生成信号
3. 传递信号给智能体
4. 处理响应

### 4.2 触发点映射

| Hook 触发点 | 适用强度 | 典型信号类型 |
|-------------|----------|--------------|
| `pre-issue-start` | block, control | `dependency-check` |
| `post-issue-start` | aid | `context-loaded` |
| `pre-tool-use` | block, control | `permission-check` |
| `post-tool-use` | aid | `result-analysis` |
| `pre-issue-submit` | block, control, prompt | `quality-gate` |
| `post-issue-submit` | aid | `review-triggered` |
| `pre-issue-close` | block | `completion-verify` |
| `post-issue-close` | aid | `retrospective` |

### 4.3 配置示例

```yaml
# .ahp/hooks.yaml

hooks:
  pre-issue-submit:
    # 触发器：提交前
    trigger: pre-issue-submit
    
    # 预言机列表（按顺序执行）
    oracles:
      - name: checklist-validator
        # 生成信号的条件和强度
        rules:
          - condition: "checklist.incomplete_count > 0"
            intensity: block
            message: "Checklist 未完成"
            
          - condition: "checklist.incomplete_count > 0 and checklist.completion_rate > 0.8"
            intensity: prompt
            message: "大部分已完成，确认提交？"
            
      - name: change-size-limiter
        rules:
          - condition: "files.changed_count > 20"
            intensity: control
            action: 
              type: split_suggestion
              max_batch: 10
              
      - name: test-gate
        rules:
          - condition: "tests.failed_count > 0"
            intensity: block
            message: "测试未通过"
            
          - condition: "coverage.current < coverage.threshold"
            intensity: prompt
            message: "覆盖率低于阈值"
```

### 4.4 执行流程

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
│ 预言机评估   │
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

---

## 5. 设计原则

### 5.1 渐进干预

优先使用低级别控制，必要时升级：

```
首次提交（Prompt）──► 未修复（Control）──► 仍违规（Block）
     ▲                                            │
     └──────────── 修复后继续 ─────────────────────┘
```

### 5.2 上下文敏感

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

### 5.3 反馈闭环

干预历史用于优化策略：

```
[干预执行] ──► [效果记录] ──► [策略分析] ──► [规则调整]
     │              │              │
     └──────────────┴──────────────┘
        （信号日志支持持续改进）
```

---

## 6. 完整示例

### 6.1 场景：Issue 提交

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

### 6.2 信号日志

```jsonl
{"timestamp": "2026-02-09T10:00:00Z", "hook": "pre-issue-submit", "intensity": "block", "source": "checklist-validator", "consumed": true, "action": "retry_after_fix"}
{"timestamp": "2026-02-09T10:15:00Z", "hook": "pre-issue-submit", "intensity": "prompt", "source": "change-size-limiter", "consumed": true, "action": "acknowledge"}
{"timestamp": "2026-02-09T10:15:01Z", "hook": "post-issue-submit", "intensity": "aid", "source": "notification", "consumed": true, "action": "suggestion_applied"}
```

---

## 7. 结论

本文定义了 AHP 的控制协议：

1. **连续控制光谱**：Block / Control / Prompt / Aid 四级干预模型
2. **信号系统**：标准化的通信格式和消费协议
3. **Hook 集成**：将控制逻辑嵌入智能体执行流程

控制协议使 AHP 能够在智能体执行过程中进行渐进式干预，而非仅依赖事后验证，从而实现质量前移和经济优化。

---

## 参考

- [02. 记录系统](./02_Record_System.md)
- [03. 智能体集成](./03_Agent_Integration.md)
