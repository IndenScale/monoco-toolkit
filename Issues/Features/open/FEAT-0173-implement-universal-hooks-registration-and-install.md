---
id: FEAT-0173
uid: '191169'
type: feature
status: open
stage: doing
title: 实现通用 Hooks 注册与安装机制
created_at: '2026-02-04T13:02:30'
updated_at: '2026-02-04T14:45:00'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0173'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Features/open/FEAT-0173-implement-universal-hooks-registration-and-install.md
- docs/zh/90_Spikes/hooks-system/README.md
- docs/zh/90_Spikes/hooks-system/agent_hooks/acl_unified_protocol_ZH.md
- docs/zh/90_Spikes/hooks-system/agent_hooks/claude_code_hooks_ZH.md
- docs/zh/90_Spikes/hooks-system/agent_hooks/gemini_cli_hooks_ZH.md
- docs/zh/90_Spikes/hooks-system/git_hooks/git_hooks_standard_ZH.md
- docs/zh/90_Spikes/hooks-system/ide_hooks/ide_hooks_standard_ZH.md
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T13:02:30'
isolation:
  type: branch
  ref: feat/feat-0173-实现通用-hooks-注册与安装机制
  created_at: '2026-02-04T13:02:56'
---

## FEAT-0173: 实现通用 Hooks 注册与安装机制

## 背景
目前 Monoco 仅支持基础的 Git Hooks（基于文件名识别），但随着功能扩展，我们需要支持多 Agent 框架（如 Claude Code, Gemini CLI）以及 IDE 场景下的钩子。原有的管理方式无法承载复杂的元数据需求（如类型细分、平台适配、动态开启等）。

## 目标
实现一套基于脚本注释 Front Matter 的通用 Hooks 注册、解析与安装机制，并将其深度集成到 `monoco sync` 流程中。

## 架构决策

基于 Spike 调研（[SPIKE-HOOKS](../../docs/zh/90_Spikes/hooks-system/README.md)），采用**类型分层 + Provider 细分**的架构：

### 1. 一级分类：Hook 类型 (type)

| 类型 | 说明 | 触发场景 |
|------|------|----------|
| `git` | 原生 Git Hooks | 提交、合并、推送等 Git 操作 |
| `ide` | IDE 集成 Hooks | 文件保存、项目打开、构建等 |
| `agent` | Agent 框架 Hooks | Agent 会话、工具调用、权限请求等 |

### 2. 二级分类：Provider 细分 (仅 agent/ide 类型)

**Agent Providers:**
| Provider | 标识符 | 配置目标 |
|----------|--------|----------|
| Claude Code | `claude-code` | `.claude/settings.json` |
| Gemini CLI | `gemini-cli` | `.gemini/settings.json` |
| (预留扩展) | `copilot-chat`, `kimi-cli` 等 | 对应配置路径 |

**IDE Providers:**
| Provider | 标识符 | 配置目标 |
|----------|--------|----------|
| VS Code | `vscode` | `.vscode/tasks.json`, `.vscode/settings.json` |
| JetBrains | `jetbrains` | `.idea/` 目录下配置 |
| Zed | `zed` | `.zed/` 或 `zed.json` |

### 3. 事件命名规范

**Git 事件** (`type: git`):
- `pre-commit`, `prepare-commit-msg`, `commit-msg`, `post-commit`
- `pre-push`, `post-merge`, `pre-rebase`

**IDE 事件** (`type: ide`):
- `on-save`, `on-open`, `on-close`, `on-build`

**Agent 事件** (`type: agent`):
- 统一命名：`session-start`, `before-tool`, `after-tool`, `before-agent`, `after-agent`
- 由 Provider 适配器映射到各自平台的具体事件名

### 4. 安装目标路径

```
.git/hooks/<event>                    # git 类型
.claude/settings.json → hooks[]       # agent 类型 + provider: claude-code
.gemini/settings.json → hooks[]       # agent 类型 + provider: gemini-cli
.vscode/tasks.json                    # ide 类型 + provider: vscode
```

### 5. 防腐层 (ACL) 设计

- **Agent Hooks 需要 ACL**: 不同 Agent 平台的 JSON 协议、字段命名、决策模型存在差异
- **Git/IDE Hooks 直接透传**: 无需协议转换，Monoco 仅负责安装和触发管理

ACL 层通过 `UniversalInterceptor` 实现：
- 输入：自动探测环境变量识别 Provider (`CLAUDE_CODE_REMOTE`, `GEMINI_ENV_FILE`)
- 处理：将 Provider 协议翻译为 Monoco 标准协议供用户脚本处理
- 输出：将用户脚本的响应翻译回 Provider 协议

## 验收标准

### 核心架构
- [ ] 实现 `UniversalHookManager` 核心类，取代单一的 `GitHooksManager`
- [ ] 实现 `HookMetadata` Pydantic 模型，字段包括：
  - [ ] 基础：`type` (git/ide/agent), `event`, `matcher`, `priority`, `description`
  - [ ] 条件：`provider` (当 type=agent 时为 claude-code/gemini-cli；当 type=ide 时为 vscode/jetbrains)
- [ ] 实现 `HookParser`，支持从脚本头部解析 YAML Front Matter（支持 `#`, `//`, `--` 注释风格）

### 分类与分发
- [ ] **Git Hooks** (`type: git`): 安装到 `.git/hooks/`，通过 `monoco-runner` 代理触发
- [ ] **Agent Hooks** (`type: agent`):
  - [ ] 按 `provider` 字段分发到对应配置
  - [ ] `provider: claude-code` → 注入 `.claude/settings.json`
  - [ ] `provider: gemini-cli` → 注入 `.gemini/settings.json`
  - [ ] 实现 `UniversalInterceptor` 运行时拦截器，自动探测 Provider 并协议转换
- [ ] **IDE Hooks** (`type: ide`):
  - [ ] `provider: vscode` → 生成 `.vscode/tasks.json` 和 `settings.json`
  - [ ] 支持 `on-save`, `on-open` 等事件

### 集成与生命周期
- [ ] 增强 `monoco sync` 命令，自动扫描 Toolkit 中的 Hooks 并按类型/Provider 安装
- [ ] 确保 `monoco uninstall` 正确清理已注入的 Hooks
- [ ] 与现有 Git Hooks 的 Marker 标记机制兼容

## 技术任务

### Phase 1: 核心模型与解析 (Foundation)
- [x] **前期调研**:
  - [x] 完成 Agent Hooks (Claude Code, Gemini CLI) 调查报告 ([acl_unified_protocol_ZH.md](../../docs/zh/90_Spikes/hooks-system/agent_hooks/acl_unified_protocol_ZH.md))
  - [x] 完善 Git Hooks 标准化方案 ([git_hooks_standard_ZH.md](../../docs/zh/90_Spikes/hooks-system/git_hooks/git_hooks_standard_ZH.md))
  - [x] 调研 IDE Hooks 集成可行性 ([ide_hooks_standard_ZH.md](../../docs/zh/90_Spikes/hooks-system/ide_hooks/ide_hooks_standard_ZH.md))
- [ ] **模型定义**:
  - [ ] 定义 `HookType` Enum: `git`, `ide`, `agent`
  - [ ] 定义 `HookMetadata` Pydantic 模型：
    - [ ] 基础字段：`type` (HookType), `event`, `matcher`, `priority`, `description`
    - [ ] Provider 字段：`provider` (Optional[str], 当 type=agent/ide 时必填)
  - [ ] 定义各类型的事件枚举：`GitEvent`, `IDEEvent`, `AgentEvent`
- [ ] **Front Matter 解析器**:
  - [ ] 实现 `HookParser` 类，从脚本头部提取 YAML Front Matter
  - [ ] 支持多语言注释风格：`#` (Shell/Python), `//` (JS/TS), `--` (Lua/SQL)
  - [ ] 实现解析错误处理和行号定位

### Phase 2: 类型分发器 (Dispatchers by Type)

#### 2.1 Git Hooks Dispatcher (`type: git`)
- [ ] 实现 `GitHookDispatcher`:
  - [ ] 安装：生成 `.git/hooks/<event>` 代理脚本，调用 `monoco hook run git <event>`
  - [ ] 支持事件：`pre-commit`, `prepare-commit-msg`, `commit-msg`, `post-merge`, `pre-push`
  - [ ] Glob matcher：基于 staged files 过滤
  - [ ] 非破坏性：与现有 Husky/pre-commit 配置共存

#### 2.2 Agent Hooks Dispatcher (`type: agent`)
- [ ] 实现 `AgentHookDispatcher`:
  - [ ] 按 `provider` 字段路由到对应子分发器
  - [ ] `ClaudeCodeDispatcher`: 注入 `.claude/settings.json` 的 `hooks` 数组
  - [ ] `GeminiDispatcher`: 注入 `.gemini/settings.json` 的 `hooks` 数组
- [ ] 实现 `UniversalInterceptor` (ACL 层):
  - [ ] Provider 自动探测（环境变量：`CLAUDE_CODE_REMOTE`, `GEMINI_ENV_FILE`）
  - [ ] `ClaudeAdapter`: 翻译 `PreToolUse` ↔ `before-tool`, `UserPromptSubmit` ↔ `before-agent`
  - [ ] `GeminiAdapter`: 翻译 `BeforeTool` ↔ `before-tool`, `BeforeAgent` ↔ `before-agent`
  - [ ] 统一决策模型：`{ decision: allow/deny/ask, reason, message }`

#### 2.3 IDE Hooks Dispatcher (`type: ide`)
- [ ] 实现 `IDEHookDispatcher`:
  - [ ] 按 `provider` 字段路由到对应子分发器
  - [ ] `VSCodeDispatcher`: 生成 `.vscode/tasks.json` 和 `settings.json`
  - [ ] 支持事件：`on-save` (codeActionsOnSave), `on-open` (folderOpen task)
  - [ ] 非阻塞设计：IDE hooks 异步执行，200ms 超时保护

### Phase 3: 管理层与集成 (Manager & Integration)
- [ ] **UniversalHookManager**:
  - [ ] 重构 `monoco/features/hooks/core.py`
  - [ ] `scan(directory)`: 递归扫描 Hook 脚本，按 `type` + `provider` 分组
  - [ ] `validate(hook)`: 校验元数据（如 type=agent 时 provider 必填）
  - [ ] `install(hook)`: 根据 type/provider 分发到对应 Dispatcher
  - [ ] `uninstall(hook)`: 从所有目标配置中移除
- [ ] **Sync 集成**:
  - [ ] 更新 `monoco/core/sync.py`，在 `sync_command` 中调用 `hook_manager.sync()`
  - [ ] 实现 Hooks 变更检测（文件哈希对比）
  - [ ] 增量安装：仅更新变更的 Hooks
- [ ] **Uninstall 清理**:
  - [ ] 更新 `monoco uninstall`，遍历所有 Dispatcher 执行清理

### Phase 4: 测试与验证 (Validation)
- [ ] **单元测试**:
  - [ ] `HookParser`: 测试各种注释风格、type/provider 组合
  - [ ] `HookMetadata`: 测试条件必填字段（type=agent 时 provider 必填）
  - [ ] 各 Dispatcher: 验证配置生成正确性
- [ ] **集成测试**:
  - [ ] 完整流程：扫描 → 解析 → 按 type/provider 分发 → 安装
  - [ ] 多类型 Hooks 共存：git + agent(claude-code) + ide(vscode) 同时安装
  - [ ] `monoco sync` 增量更新测试
- [ ] **ACL 测试**:
  - [ ] `UniversalInterceptor` 正确识别 Provider
  - [ ] 协议翻译正确性（输入/输出双向）
- [ ] **兼容性测试**:
  - [ ] Git Hooks 与 Husky 共存
  - [ ] 与现有 `monoco issue` Hooks 兼容

## Review Comments
<!-- 评审阶段时填写 -->
