# 3.1 AGENTS.md：上下文配置

## 摘要

`AGENTS.md` 是 AHP 与智能体交互的第一接触点，作为项目级的"宪法"，向智能体注入规则、偏好和上下文信息，确保智能体在正确的约束下工作。

---

## 1. 核心概念

### 1.1 什么是 AGENTS.md

`AGENTS.md` 是一个 Markdown 格式的配置文件，定义了：

- **项目背景与结构**：架构概览、目录组织
- **编码规范与约束**：命名约定、导入规则、代码风格
- **工作流规则**：Git 规范、分支策略、提交流程
- **角色定义**：不同场景下的行为偏好

### 1.2 与 README.md 的区别

| 特性 | README.md | AGENTS.md |
|------|-----------|-----------|
| **目标读者** | 人类开发者 | LLM 智能体 |
| **内容重点** | 项目介绍、快速开始 | 行为规则、约束条件 |
| **更新频率** | 低频（项目稳定后） | 中频（随规则演进） |
| **格式风格** | 自由文本 | 结构化、指令式 |

---

## 2. 文件位置与继承

### 2.1 多级配置体系

支持多级配置，按就近原则继承：

```
~/AGENTS.md                    # 用户级默认
  ↓ (继承并覆盖)
/workspace/AGENTS.md           # 项目级规则
  ↓ (继承并覆盖)
/workspace/subdir/AGENTS.md    # 子目录特定规则
```

### 2.2 继承规则

1. **字段合并**：子级文件补充父级未定义的字段
2. **显式覆盖**：子级明确定义的字段覆盖父级
3. **累加列表**：如 `skills`、`ignore_patterns` 等列表类型字段累加

### 2.3 典型目录结构

```
project/
├── AGENTS.md              # 项目级主配置
├── docs/
│   └── AGENTS.md          # 文档目录特定规则
├── src/
│   └── AGENTS.md          # 源代码目录规则
└── .ahp/
    └── AGENTS.local.md    # 本地覆盖（gitignored）
```

---

## 3. 内容结构规范

### 3.1 标准模板

```markdown
<!-- AGENTS.md 标准模板 -->

# [项目名称] - Agent 上下文

## 1. 项目概览

### 1.1 架构
- 架构风格：[分层/微服务/事件驱动]
- 主要技术栈：[语言/框架/数据库]
- 关键目录结构：
  - `src/domain/`：领域层
  - `src/application/`：应用层
  - `src/infrastructure/`：基础设施层

### 1.2 核心依赖
- 外部服务：API、数据库等
- 内部模块：核心库、工具函数

## 2. 编码规范

### 2.1 命名约定
| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | snake_case | `user_service.py` |
| 类 | PascalCase | `UserService` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| 函数 | snake_case | `get_user_by_id()` |

### 2.2 导入规则
1. 标准库
2. 第三方库
3. 本项目模块（绝对导入）

### 2.3 代码风格
- 缩进：4 空格
- 行长度：100 字符
- 类型注解：必填

## 3. 工作流规则

### 3.1 Git 规范
- 分支策略：Trunk Based Development
- 禁止直接在 main 分支修改
- Issue 必须关联分支
- 提交信息格式：`type(scope): message`

### 3.2 测试要求
- 新功能必须有单元测试
- 测试覆盖率不得低于 80%
- 集成测试放在 `tests/integration/`

### 3.3 代码审查
- 所有提交需通过 PR
- 至少 1 个审批
- CI 检查通过

## 4. 特殊规则

### 4.1 安全约束
- 禁止在代码中硬编码密钥
- 用户输入必须验证和转义
- 敏感操作需审计日志

### 4.2 性能约束
- 数据库查询需有索引
- 批量操作限制 1000 条/次
- 缓存策略：TTL 300s

## 5. 上下文变量

### 5.1 环境变量
```bash
NODE_ENV=production
DEBUG=false
API_BASE_URL=https://api.example.com
```

### 5.2 常用命令
```bash
# 运行测试
npm test

# 代码检查
npm run lint

# 构建
npm run build
```
```

### 3.2 必需字段

| 章节 | 说明 | 重要性 |
|------|------|--------|
| 项目概览 | 架构、技术栈、目录结构 | 高 |
| 编码规范 | 命名、导入、风格 | 高 |
| 工作流规则 | Git、测试、审查 | 高 |
| 特殊规则 | 安全、性能约束 | 中 |

---

## 4. 动态上下文生成

### 4.1 上下文组装流程

当智能体启动 Issue 时，AHP 动态组装上下文：

```python
def build_agent_context(issue: IssueTicket) -> str:
    """构建智能体上下文"""
    context_parts = [
        load_agents_md(),           # 项目级配置
        load_issue_context(issue),  # Issue 详情
        load_related_files(issue),  # 关联文件内容
    ]
    return "\n\n---\n\n".join(context_parts)
```

### 4.2 上下文片段示例

```markdown
<!-- AGENTS.md 加载的内容 -->
# 项目概览

本项目采用分层架构...

---

<!-- Issue 详情 -->
# Issue FEAT-0123: 实现用户登录

## 描述
添加基于 JWT 的用户认证系统

## Checklist
- [x] 设计数据库 Schema
- [ ] 实现登录 API
- [ ] 编写单元测试

---

<!-- 关联文件 -->
## 相关文件

### src/models/user.py
```python
class User(Base):
    id: int
    email: str
    password_hash: str
```
```

---

## 5. 最佳实践

### 5.1 编写建议

1. **具体而非抽象**
   - ❌ "编写干净的代码"
   - ✅ "函数长度不超过 50 行，复杂度不超过 10"

2. **提供示例**
   - 每个规范都配上代码示例
   - 展示正确和错误的对比

3. **分层组织**
   - 从宏观到微观
   - 先架构，再规范，最后具体规则

4. **保持更新**
   - 技术栈变更时同步更新
   - 新约束及时添加

### 5.2 常见模式

#### 技术栈声明

```markdown
## 技术栈

### 后端
- **语言**：Python 3.11+
- **框架**：FastAPI 0.100+
- **ORM**：SQLAlchemy 2.0+
- **数据库**：PostgreSQL 15+

### 前端
- **框架**：React 18+
- **状态管理**：Zustand
- **样式**：Tailwind CSS
```

#### 架构约束

```markdown
## 架构约束

### 依赖规则
- Domain 层不依赖任何外部层
- Application 层仅依赖 Domain
- Infrastructure 层可依赖所有上层

### 禁止事项
- 禁止在 Domain 层使用 `datetime.now()`，使用注入的 Clock
- 禁止 Repository 直接返回 ORM 对象，必须转换为 Domain 模型
```

---

## 6. 与其他机制的关系

### 6.1 与 Hooks 的关系

```
AGENTS.md          Hooks
    │                │
    ▼                ▼
定义规则          强制执行
"使用 TBD"        禁止 main 分支提交
"测试覆盖 80%"    pre-issue-submit 检查
```

AGENTS.md 定义规则，Hooks 在关键点强制执行。

### 6.2 与 Skills 的关系

```
AGENTS.md          Skills
    │                │
    ▼                ▼
说明可用工具      提供工具实现
"使用 monoco-issue"  `monoco issue` 命令
```

AGENTS.md 说明可用的 Skills，Skills 提供具体实现。

---

## 7. 示例：完整的 AGENTS.md

```markdown
# E-Commerce API - Agent 上下文

## 1. 项目概览

### 1.1 架构
- **风格**： Clean Architecture + CQRS
- **技术栈**：Python 3.11, FastAPI, PostgreSQL, Redis
- **部署**：Docker + Kubernetes

### 1.2 目录结构
```
src/
├── domain/          # 领域层：实体、值对象、领域事件
├── application/     # 应用层：用例、命令、查询
├── infrastructure/  # 基础设施：ORM、API、外部服务
└── interfaces/      # 接口层：控制器、DTO
```

## 2. 编码规范

### 2.1 Python 规范
- 遵循 PEP 8
- 使用 Black 格式化
- 类型注解覆盖率 100%

### 2.2 导入顺序
```python
# 1. 标准库
from datetime import datetime

# 2. 第三方库
from fastapi import APIRouter

# 3. 本项目（按层级）
from domain.models import User
from application.services import UserService
```

### 2.3 错误处理
- 使用自定义异常类
- 不在 Domain 层使用 try-except
- API 层统一捕获并转换

## 3. 工作流规则

### 3.1 Git
- 使用 Trunk Based Development
- 分支命名：`feat/FEAT-XXX-short-desc`
- 提交信息：`feat(auth): add JWT login [FEAT-0123]`

### 3.2 测试
- 单元测试覆盖率 ≥ 80%
- 集成测试覆盖关键路径
- 使用 pytest + pytest-asyncio

### 3.3 Issue 管理
- 使用 `monoco issue` 命令
- 启动前确保 checklist 完整
- 提交前运行 `monoco issue lint`

## 4. 安全约束

- API 密钥使用环境变量
- 密码使用 bcrypt 哈希
- JWT 过期时间 1 小时
- 敏感接口需要 rate limiting

## 5. 性能约束

- 数据库查询需 EXPLAIN 验证
- API 响应时间 < 200ms (p99)
- 批量操作限制 1000 条/次
```

---

## 参考

- [3.2 Agent Hooks](./02_Agent_Hooks.md)
- [3.3 Agent Skills](./03_Agent_Skills.md)
- [04. 控制协议](../04_Control_Protocol.md)
