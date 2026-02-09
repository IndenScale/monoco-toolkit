# 3.3 Agent Skills：能力扩展

## 摘要

Skills 是智能体可调用的工具包，封装领域特定的操作能力。通过标准化的接口定义，Skills 将 AHP 的功能以工具形式暴露给智能体，实现能力的模块化扩展。

---

## 1. 核心概念

### 1.1 什么是 Agent Skills

Agent Skills 是 AHP 提供的扩展机制：

- **能力封装**：将领域操作封装为可调用工具
- **标准化接口**：统一的调用约定和返回格式
- **动态发现**：运行时加载和注册
- **权限控制**：细粒度的访问控制

### 1.2 与 Function Calling 的关系

| 层面 | Function Calling | Agent Skills |
|------|------------------|--------------|
| **定位** | LLM 底层能力 | AHP 应用层封装 |
| **范围** | 通用工具调用 | 领域特定操作 |
| **上下文** | 无状态 | 完整的 AHP 上下文感知 |
| **示例** | `ReadFile`, `Bash` | `monoco issue start`, `monoco memo add` |

---

## 2. Skill 结构

### 2.1 文件组织

每个 Skill 是一个目录，包含：

```
skills/
└── skill-name/
    ├── SKILL.md          # 使用文档与示例
    ├── schema.yaml       # 参数与返回值定义
    ├── hooks.yaml        # Skill 级 Hooks（可选）
    └── src/              # 实现代码
        ├── __init__.py
        └── tools/
            ├── tool_a.py
            └── tool_b.py
```

### 2.2 SKILL.md 规范

```markdown
# Skill: skill-name

## 描述
一句话描述 Skill 的功能。

## 使用场景
- 场景 1：...
- 场景 2：...

## 可用工具

### tool-name
**描述**：工具功能描述

**参数**：
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| param1 | string | 是 | 参数说明 |
| param2 | number | 否 | 参数说明，默认 10 |

**返回值**：
| 字段 | 类型 | 描述 |
|------|------|------|
| result | string | 操作结果 |
| data | object | 详细数据 |

**示例**：
```python
# 调用示例
result = skill.tool_name(param1="value", param2=20)
```

## 最佳实践
1. 建议 1
2. 建议 2

## 注意事项
- 注意点 1
- 注意点 2
```

### 2.3 Schema.yaml 规范

```yaml
# schema.yaml

name: skill-name
description: Skill 描述
version: 1.0.0
author: AHP Team
category: [issue-management, documentation, testing]

tools:
  - name: create
    description: 创建新 Issue
    parameters:
      type:
        type: string
        enum: [feature, fix, chore, docs, refactor]
        description: Issue 类型
      title:
        type: string
        minLength: 5
        maxLength: 100
        description: Issue 标题
      description:
        type: string
        description: 详细描述
      labels:
        type: array
        items:
          type: string
        description: 标签列表
        default: []
    returns:
      issue_id:
        type: string
        description: 生成的 Issue ID
      file_path:
        type: string
        description: Issue 文件路径
      branch_name:
        type: string
        description: 建议的分支名称
        
  - name: start
    description: 启动 Issue
    parameters:
      id:
        type: string
        description: Issue ID
      branch:
        type: boolean
        description: 是否创建分支
        default: true
      worktree:
        type: boolean
        description: 是否使用 worktree
        default: false
    returns:
      branch_name:
        type: string
        description: 分支名称
      files:
        type: array
        items:
          type: string
        description: 关联文件列表
      worktree_path:
        type: string
        description: worktree 路径（如适用）
```

---

## 3. 内置 Skills

### 3.1 monoco-issue：Issue 生命周期管理

| 工具 | 功能 | 示例调用 |
|------|------|----------|
| `create` | 创建新 Issue | `monoco issue create feature -t "登录功能"` |
| `start` | 启动 Issue | `monoco issue start FEAT-0123 --branch` |
| `sync-files` | 同步文件变更 | `monoco issue sync-files` |
| `submit` | 提交 Issue | `monoco issue submit FEAT-0123` |
| `close` | 关闭 Issue | `monoco issue close FEAT-0123` |
| `lint` | 检查 Issue 完整性 | `monoco issue lint FEAT-0123` |

**使用场景**：

```python
# 场景 1：开始新任务
agent.use_skill("monoco-issue", "create", {
    "type": "feature",
    "title": "实现用户登录",
    "description": "添加 JWT 认证..."
})

# 场景 2：启动已创建的 Issue
agent.use_skill("monoco-issue", "start", {
    "id": "FEAT-0123",
    "branch": True
})

# 场景 3：提交完成的工作
agent.use_skill("monoco-issue", "submit", {
    "id": "FEAT-0123"
})
```

### 3.2 monoco-memo：快速笔记捕获

| 工具 | 功能 | 示例调用 |
|------|------|----------|
| `add` | 添加 Memo | `monoco memo add "需要优化查询性能" -c database` |
| `list` | 列出待处理 Memo | `monoco memo list` |
| `delete` | 删除 Memo | `monoco memo delete MEMO-001` |
| `open` | 打开 inbox | `monoco memo open` |

**使用场景**：

```python
# 场景：记录临时想法
agent.use_skill("monoco-memo", "add", {
    "content": "数据库查询需要添加索引",
    "context": "performance"
})

# 稍后查看待处理事项
memos = agent.use_skill("monoco-memo", "list")
# 输出：["MEMO-001: 数据库查询需要添加索引"]
```

### 3.3 monoco-spike：外部仓库引用

| 工具 | 功能 | 示例调用 |
|------|------|----------|
| `add` | 添加外部仓库 | `monoco spike add https://github.com/example/repo` |
| `sync` | 同步引用内容 | `monoco spike sync` |
| `list` | 列出引用 | `monoco spike list` |
| `remove` | 移除引用 | `monoco spike remove repo-name` |

**使用场景**：

```python
# 场景：参考开源实现
agent.use_skill("monoco-spike", "add", {
    "url": "https://github.com/awesome-auth/jwt-auth",
    "name": "jwt-reference"
})

# 查看引用
agent.use_skill("monoco-spike", "list")
# 输出：["jwt-reference: https://github.com/..."]
```

### 3.4 monoco-i18n：国际化管理

| 工具 | 功能 | 示例调用 |
|------|------|----------|
| `scan` | 扫描缺失翻译 | `monoco i18n scan` |
| `sync` | 同步翻译文件 | `monoco i18n sync` |
| `check` | 检查翻译完整性 | `monoco i18n check` |

### 3.5 monoco-lint：代码检查

| 工具 | 功能 | 示例调用 |
|------|------|----------|
| `run` | 运行所有 linter | `monoco lint run` |
| `fix` | 自动修复问题 | `monoco lint fix` |
| `check` | 检查特定规则 | `monoco lint check import-order` |

---

## 4. Skill 发现与加载

### 4.1 加载路径

AHP 从以下位置加载 Skills：

```
1. 内置 Skills：~/.ahp/skills/          # AHP 官方提供
2. 项目 Skills：./.ahp/skills/          # 项目自定义
3. 用户 Skills：~/.config/ahp/skills/   # 用户个人
```

加载顺序：内置 → 项目 → 用户（后加载的覆盖先加载的）

### 4.2 发现机制

```python
class SkillRegistry:
    """Skill 注册表"""
    
    def discover_skills(self) -> list[Skill]:
        """发现所有可用 Skills"""
        skills = []
        
        for search_path in self.search_paths:
            for skill_dir in search_path.glob("*/"):
                if (skill_dir / "schema.yaml").exists():
                    skill = self._load_skill(skill_dir)
                    skills.append(skill)
        
        return skills
    
    def get_skill(self, name: str) -> Skill | None:
        """按名称获取 Skill"""
        return self._skills.get(name)
```

### 4.3 动态加载

```python
# 运行时加载新 Skill
ahp.load_skill("/path/to/custom-skill")

# 重新加载已修改的 Skill
ahp.reload_skill("monoco-issue")
```

---

## 5. Skill 开发

### 5.1 创建新 Skill

```bash
# 使用 CLI 创建模板
monoco skill create my-skill --template python

# 生成目录结构
my-skill/
├── SKILL.md
├── schema.yaml
├── hooks.yaml
└── src/
    ├── __init__.py
    └── tools/
        └── __init__.py
```

### 5.2 实现示例

```python
# src/tools/__init__.py
from ahp import Skill, tool

class MySkill(Skill):
    """自定义 Skill 示例"""
    
    @tool
    def analyze_code(self, file_path: str, rules: list[str] = None) -> dict:
        """
        分析代码质量。
        
        Args:
            file_path: 要分析的文件路径
            rules: 要检查的规则列表
            
        Returns:
            分析结果
        """
        # 实现逻辑
        issues = self._run_analysis(file_path, rules)
        
        return {
            "file": file_path,
            "issues": issues,
            "score": self._calculate_score(issues)
        }
    
    @tool
    def fix_issues(self, file_path: str, issue_ids: list[str] = None) -> dict:
        """自动修复代码问题"""
        # 实现逻辑
        fixes = self._apply_fixes(file_path, issue_ids)
        
        return {
            "file": file_path,
            "fixes_applied": len(fixes),
            "details": fixes
        }
```

### 5.3 注册与使用

```python
# __init__.py
from .tools import MySkill

# 导出 Skill 类
__all__ = ["MySkill"]
```

使用：

```python
# 智能体调用
result = agent.use_skill("my-skill", "analyze_code", {
    "file_path": "src/main.py",
    "rules": ["unused-imports", "complexity"]
})
```

---

## 6. Skill 与 Hooks 的关系

### 6.1 对比

| 维度 | Skills | Hooks |
|------|--------|-------|
| **触发方式** | 智能体主动调用 | 事件被动触发 |
| **控制权** | 智能体掌握 | AHP 掌握 |
| **用途** | 扩展能力 | 约束与引导 |
| **返回值** | 操作结果 | 干预信号 |
| **执行时机** | 按需 | 预设触发点 |

### 6.2 协作关系

```
智能体
  │
  ├─► 调用 Skill ──► 执行操作 ──► 返回结果
  │                     │
  │                     ▼
  │               触发 Hook
  │               （如 post-tool）
  │                     │
  │                     ▼
  └──────────────── 接收信号
                    （如需干预）
```

### 6.3 互补示例

```python
# 智能体调用 Skill
result = agent.use_skill("monoco-issue", "submit", {"id": "FEAT-0123"})

# 内部流程：
# 1. Skill 执行提交逻辑
# 2. 触发 pre-issue-submit Hook
# 3. Hook 检查 checklist（ChecklistValidator）
# 4. 发现未完成项，返回 block 信号
# 5. Skill 返回错误结果，智能体收到反馈

# 智能体响应反馈
agent.fix_issues(["完成 API 文档"])
agent.use_skill("monoco-issue", "submit", {"id": "FEAT-0123"})
# 这次通过，提交成功
```

---

## 7. Skill 级 Hooks

### 7.1 概念

每个 Skill 可以定义自己的 Hooks，在 Skill 调用前后执行：

```yaml
# my-skill/hooks.yaml

hooks:
  pre-invoke:
    # 在 Skill 工具调用前执行
    - oracle: ParameterValidator
      config:
        schema: "${skill.schema}"
        
  post-invoke:
    # 在 Skill 工具调用后执行
    - oracle: ResultFormatter
      config:
        format: "json"
```

### 7.2 用途

- **参数验证**：确保输入符合 schema
- **权限检查**：验证智能体有权限调用
- **结果处理**：格式化、缓存、日志
- **副作用**：发送通知、更新状态

---

## 8. 最佳实践

### 8.1 Skill 设计原则

1. **单一职责**：每个 Skill 专注于一个领域
2. **原子操作**：工具粒度适中，可组合使用
3. **幂等性**：相同输入产生相同结果，可重复调用
4. **清晰文档**：SKILL.md 包含完整使用说明

### 8.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| Skill 名称 | kebab-case，前缀 | `monoco-issue`, `myproject-deploy` |
| 工具名称 | snake_case | `create`, `start`, `sync_files` |
| 参数名称 | snake_case | `issue_id`, `create_branch` |

### 8.3 错误处理

```python
@tool
def my_tool(self, param: str) -> dict:
    try:
        result = self._do_work(param)
        return {
            "success": True,
            "data": result
        }
    except ValidationError as e:
        return {
            "success": False,
            "error": {
                "type": "validation_error",
                "message": str(e),
                "suggestions": e.suggestions
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": {
                "type": "internal_error",
                "message": "操作失败，请重试"
            }
        }
```

---

## 参考

- [3.1 AGENTS.md](./01_AGENTS_md.md)
- [3.2 Agent Hooks](./02_Agent_Hooks.md)
- [04. 控制协议](../04_Control_Protocol.md)
