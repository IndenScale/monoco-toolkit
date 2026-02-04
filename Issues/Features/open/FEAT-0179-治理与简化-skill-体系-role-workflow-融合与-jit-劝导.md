---
id: FEAT-0179
uid: 283ca5
type: feature
status: open
stage: draft
title: 治理与简化 Skill 体系：Role/Workflow 融合与 JIT 劝导
created_at: '2026-02-04T20:40:16'
updated_at: '2026-02-04T22:15:00'
parent: EPIC-0030
dependencies:
- CHORE-0039
related: []
domains:
- DevEx
- AgentEmpowerment
tags:
- '#EPIC-0030'
- '#FEAT-0179'
files:
- .gemini/skills/
- .claude/skills/
- AGENTS.md
- monoco/core/sync.py
- monoco/core/injection.py
- monoco/features/hooks/
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T20:40:16'
---

## FEAT-0179: 治理与简化 Skill 体系：Role/Workflow 融合与 JIT 劝导

## Objective
通过消除 Role、Workflow 和 Atom 技能之间的逻辑冗余，显著精简 Skill 体系。引入基于 Hooks 的 JIT 劝导机制，将静态规则约束转变为动态环境反馈，提升 Agent 执行效率。

---

## Investigation Summary (2026-02-04)

### 1. Monoco Hooks 系统架构

#### 1.1 双层 Hooks 架构

| 层级 | 路径 | 职责 | 触发时机 |
|------|------|------|----------|
| **Universal Hooks** | `monoco/features/hooks/` | 跨平台 Hook 分发与管理 | Git/Agent/IDE 事件 |
| **Session Lifecycle Hooks** | `monoco/core/hooks/` | 会话级生命周期管理 | Session start/end |

#### 1.2 Universal Hooks 核心组件

```
monoco/features/hooks/
├── models.py              # HookType (git/ide/agent), AgentEvent, HookMetadata
├── manager.py             # UniversalHookManager - 扫描、验证、组织 hooks
├── universal_interceptor.py  # ACL 协议转换层
├── dispatchers/
│   ├── git_dispatcher.py  # Git hooks 分发 (pre-commit, pre-push 等)
│   └── agent_dispatcher.py # Agent hooks 分发 (Claude Code, Gemini CLI)
└── resources/hooks/       # 内置 hooks 存储
```

**AgentEvent 类型** (JIT 劝导的关键注入点):
- `session-start` - 会话开始时注入角色上下文
- `before-tool` - 工具调用前检查/劝导 (如 Bash 命令)
- `after-tool` - 工具调用后记录/反馈
- `before-agent` - Agent 处理前注入指令
- `after-agent` - Agent 响应后处理
- `session-end` - 会话结束清理

#### 1.3 Session Lifecycle Hooks (核心层)

```python
# monoco/core/hooks/base.py
class SessionLifecycleHook(ABC):
    def on_session_start(self, context: HookContext) -> HookResult
    def on_session_end(self, context: HookContext) -> HookResult

# monoco/core/hooks/context.py 包含:
- IssueInfo: id, status, stage, branch_name, is_merged
- GitInfo: current_branch, has_uncommitted_changes
```

### 2. Sync 配置注入机制

#### 2.1 `monoco sync` 执行流程 (`monoco/core/sync.py`)

```
sync_command()
├── 1. FeatureRegistry.load_defaults()     # 加载所有 feature
├── 2. 收集 system_prompts (来自各 feature.integrate())
├── 3. distribute_roles()                  # 同步 .monoco/roles/
├── 4. SkillManager.distribute()           # 分发到 .gemini/skills/, .claude/skills/
├── 5. distribute_workflows()              # (可选) 分发到 .agent/workflows/
├── 6. Universal Hooks 同步
│   ├── scan builtin hooks (features/hooks/resources/hooks/)
│   ├── scan feature hooks (features/*/resources/hooks/)
│   ├── GitHookDispatcher.sync()           # 安装到 .git/hooks/
│   └── AgentHookDispatcher.sync()         # 注入到 .claude/settings.json, .gemini/settings.json
└── 7. PromptInjector.inject()             # 更新 GEMINI.md, CLAUDE.md
```

#### 2.2 Prompt 注入机制 (`monoco/core/injection.py`)

```python
class PromptInjector:
    MANAGED_HEADER = "## Monoco Toolkit"
    MANAGED_START = "<!-- MONOCO_GENERATED_START -->"
    MANAGED_END = "<!-- MONOCO_GENERATED_END -->"
    
    def inject(self, prompts: Dict[str, str]) -> bool:
        # 将 prompts 注入目标文件的 Managed Block 中
```

**特点**:
- 使用 HTML 注释标记管理区块
- 支持内容头降级 (demote headers)
- 保留用户手动添加的内容

#### 2.3 Agent Hooks 配置注入格式

**Claude Code** (`.claude/settings.json`):
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "monoco hook run agent before-tool",
        "_monoco_managed": true,
        "_monoco_hook_id": "branch-check"
      }]
    }]
  }
}
```

**Gemini CLI** (`.gemini/settings.json`):
```json
{
  "hooks": {
    "BeforeTool": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command", 
        "command": "monoco hook run agent before-tool",
        "_monoco_managed": true
      }]
    }]
  }
}
```

#### 2.4 ACL 协议转换 (`universal_interceptor.py`)

```
Agent Event → UniversalInterceptor → UnifiedDecision
                              ↓
                    metadata.additionalContext
                              ↓
                    动态劝导信息注入
```

**UnifiedDecision 结构**:
```python
@dataclass
class UnifiedDecision:
    decision: str       # "allow", "deny", "ask"
    reason: str
    message: str
    metadata: dict      # ← JIT 劝导的关键字段，可包含 additionalContext
```

### 3. Skill 体系现状分析

#### 3.1 当前冗余结构

| 类型 | 数量 | 示例 | 问题 |
|------|------|------|------|
| **Atom** | 11 | `monoco_atom_code_dev`, `monoco_atom_issue` | 过于碎片化，功能重叠 |
| **Role** | 4 | `monoco_role_engineer`, `monoco_role_manager` | 缺少动态上下文 |
| **Workflow** | 9 | `monoco_workflow_agent_engineer` | 与 Role 逻辑重复 |

**重复案例**:
- `monoco_role_engineer` vs `monoco_workflow_agent_engineer`: 都定义 Engineer 角色职责
- `monoco_atom_issue` + `monoco_atom_issue_lifecycle` vs Issue Feature 本身

#### 3.2 JIT 劝导可替代的场景

| 当前静态 Skill | JIT 替代方案 | 触发 Hook |
|----------------|--------------|-----------|
| "提交前必须运行 sync-files" | 检测 `git commit` 前是否有未同步文件 | `pre-commit` |
| "在 Feature 分支才能修改代码" | 检测当前分支是否为 feature/* | `before-tool` (Bash) |
| "代码修改后更新 tests" | 检测文件变更并提醒 | `after-tool` (WriteFile) |
| "Start Issue 必须带 --branch" | 检测 `monoco issue start` 参数 | `before-tool` |

### 4. JIT 劝导实现方案

#### 4.1 推荐的 Hook 部署策略

**阶段 1: before-tool 劝导** (高优先级)
```yaml
# 示例: features/issue/resources/hooks/before-tool.sh
---
type: agent
provider: claude-code
event: before-tool
matcher: ["Bash", "WriteFile"]
priority: 10
description: "检查代码修改合规性"
---
# 脚本内容：检测是否在正确的分支、是否已 sync-files
```

**阶段 2: session-start 上下文注入**
```yaml
# 示例: features/issue/resources/hooks/session-start.sh
---
type: agent
provider: claude-code  
event: session-start
priority: 5
description: "注入当前 Issue 上下文"
---
# 脚本内容：读取当前 Issue 状态，通过 additionalContext 注入
```

#### 4.2 JIT 注入协议

Hook 脚本可通过 stdout 返回 JSON:
```json
{
  "decision": "allow",
  "reason": "Branch check passed",
  "message": "当前在 feature/FEAT-0179 分支，可以安全修改代码",
  "metadata": {
    "additionalContext": {
      "current_issue": "FEAT-0179",
      "current_stage": "in_progress",
      "reminders": ["记得在提交前运行 monoco issue sync-files"]
    }
  }
}
```

---

## Acceptance Criteria
- [ ] `.gemini/skills` `.claude/skills` 目录下的冗余技能（Workflow/Atom）被移除
- [ ] Role 技能整合了必要的工作流逻辑，初始化速度提升
- [ ] `AGENTS.md` 中的资源声明得到简化
- [ ] 实现至少一个工作流阶段的 JIT 劝导（如：start 分支检查）

## Technical Tasks
- [ ] **Skill 融合**: 将 `monoco_workflow_agent_*` 逻辑合并入 `monoco_role_*`
- [ ] **清理冗余**: 删除所有 `monoco_atom_*` 技能文件
- [ ] **重构 AGENTS.md**: 简化角色资源配置，移除对已删除技能的引用
- [ ] **实现 JIT 注入**: 基于 CHORE-0039 的设计，在关键工具调用前后注入劝导信息
  - [ ] 创建 `features/issue/resources/hooks/before-tool.sh` - 分支检查劝导
  - [ ] 创建 `features/issue/resources/hooks/session-start.sh` - Issue 上下文注入
  - [ ] 验证 `universal_interceptor.py` 的 additionalContext 传递

## Implementation Notes

### 关键代码路径
1. **Hooks 扫描**: `monoco/core/sync.py:216-251` - 扫描各 feature 的 resources/hooks/
2. **Agent 配置注入**: `monoco/features/hooks/dispatchers/agent_dispatcher.py:186-231`
3. **协议转换**: `monoco/features/hooks/universal_interceptor.py:412-478` - _execute_hook 方法

### 依赖准备
- CHORE-0039 已完成，ACL 层已就绪
- 需确保 `.claude/settings.json` 和 `.gemini/settings.json` 的 hooks 字段支持

### 风险评估
| 风险 | 缓解措施 |
|------|----------|
| JIT 劝导延迟影响体验 | 设置 timeout (当前 5min)，复杂检查异步执行 |
| 过多 hooks 导致混乱 | 优先级排序 (priority 字段)，支持条件禁用 |
| Agent 框架不支持 hooks | 优雅降级，继续使用静态 skills |

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->