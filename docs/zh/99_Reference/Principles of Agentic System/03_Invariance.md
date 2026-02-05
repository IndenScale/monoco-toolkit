# 03. 体系不变量(System Invariance)

## 1. 动态位移中的守恒定律

在自主智能体系统中,代码库被视为一个处于不断"动态位移"中的逻辑流形。智能体在执行任务时,会对该流形施加各种修改力。如果这种修改力是不受控的,系统很快会滑向混乱和崩溃。为了保障系统的长期健康,我们必须确立一系列"体系不变量"(System Invariance)。

体系不变量是在系统状态发生任何变更的前后,必须始终保持为 True 的逻辑判定。它不同于针对特定任务的完成标准(DoD),它是跨越所有任务的、全局性的合法性判据。在物理学中,守恒定律描述了闭合系统在演化中不变的量;在智能体系统中,体系不变量描述了代码库在演化中必须维持的"尊严"和"秩序"。

基于对 Monoco Issue 模块、Git Hooks、pytest/ruff 等静态分析框架以及 Typedown 的深入调研,我们识别出三种核心不变性:

## 2. 三种核心不变性

### 2.1 开发流程不变性(Process Invariance)

开发流程不变性确保智能体的工作流程始终遵循既定的工程规范,防止智能体绕过质量门禁或破坏协作协议。

#### 实现机制:Issue Lifecycle Hooks

Monoco 通过 **Issue Lifecycle Hooks** 系统实现流程不变性。该系统在 Issue 生命周期的关键节点注入强制性检查:

```python
# monoco/features/issue/hooks/models.py
class IssueEvent(Enum):
    PRE_CREATE = "pre-issue-create"
    POST_CREATE = "post-issue-create"
    PRE_START = "pre-issue-start"
    POST_START = "post-issue-start"
    PRE_SUBMIT = "pre-issue-submit"
    POST_SUBMIT = "post-issue-submit"
    PRE_CLOSE = "pre-issue-close"
    POST_CLOSE = "post-issue-close"
```

**关键护栏示例**:

1. **Pre-Submit Hook**: 在智能体提交 Issue 前,自动执行 `sync-files` 和 `lint` 检查

   ```python
   # monoco/features/issue/hooks/builtin/__init__.py
   def pre_submit_hook(context: "IssueHookContext") -> "IssueHookResult":
       # 自动同步文件列表
       sync_issue_files(issues_root, issue_id, project_root)

       # 执行 Lint 检查
       diagnostics = check_integrity(issues_root, recursive=False)

       if issue_diags:
           return IssueHookResult.deny(
               f"Issue {issue_id} failed lint validation",
               diagnostics=hook_diags
           )
   ```

2. **Post-Create Hook**: 创建 Issue 后立即反馈缺失字段
   ```python
   def post_create_hook(context: "IssueHookContext") -> "IssueHookResult":
       diagnostics = check_integrity(issues_root, recursive=True)
       suggestions = [
           "Please fill in 'Acceptance Criteria' and 'Technical Tasks'",
           f"You can view the issue with: monoco issue inspect {issue_id}"
       ]
   ```

#### 流程不变性的价值

- **防止半成品提交**: 智能体无法在未完成必填字段的情况下提交 Issue
- **强制文件追踪**: 确保所有代码变更都被记录在 Issue 的 `files` 字段中
- **自动质量反馈**: 在流程的每个阶段提供即时的诊断信息

### 2.2 代码产物不变性(Artifact Invariance)

代码产物不变性确保智能体生成的代码始终满足语法正确性、风格一致性和测试覆盖率等基础质量标准。

#### 实现机制:Git Hooks + 静态分析

Monoco 通过 **Git Pre-commit Hooks** 集成 `pytest` 和 `ruff` 等工具,在代码提交前执行强制性检查:

```bash
# .git/hooks/pre-commit (自动生成)
#!/bin/sh
# MONOCO_HOOK_MARKER: git-pre-commit

# 检查暂存文件是否匹配 Issues/**/*.md 模式
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
if [ "$MATCHED" = "true" ]; then
    # 执行 Monoco hook
    exec uv run python3 -m monoco hook run git pre-commit "$@"
fi
```

**质量门禁层次**:

1. **语法层(L0)**: Ruff Linter 检查

   ```toml
   # pyproject.toml
   [tool.ruff.lint]
   ignore = ["E402", "E722", "F811", "F841", "E741"]
   ```

2. **语义层(L1)**: Pytest 单元测试

   ```toml
   [tool.pytest.ini_options]
   asyncio_mode = "auto"
   testpaths = ["tests"]
   norecursedirs = ["tests/legacy", "Archives", ".git", ".venv"]
   ```

3. **结构层(L2)**: Issue Linter 检查
   ```python
   # monoco/features/issue/linter.py
   def check_integrity(issues_root: Path, recursive: bool = False) -> List[Diagnostic]:
       """验证 Issues 目录的完整性"""
       # 1. 收集阶段:构建索引
       # 2. 验证阶段:执行多维度检查
       #    - ID 唯一性
       #    - 文件名一致性
       #    - 域治理(Domain Governance)
       #    - 引用完整性
   ```

#### 代码产物不变性的价值

- **零容忍破坏性变更**: 任何导致测试失败的代码都无法进入主干
- **风格一致性**: 通过 Ruff 强制执行统一的代码风格
- **结构完整性**: Issue Linter 确保所有 Issue 文件符合 Schema 规范

### 2.3 系统状态不变性(State Invariance)

系统状态不变性是最高层次的不变性,它确保系统的业务逻辑约束在任何时刻都得到满足。传统系统通过数据库约束(如外键、触发器)实现状态不变性,但这种方式存在以下局限:

- **约束分散**: 业务规则散落在 SQL、ORM、应用代码中
- **版本控制缺失**: 数据库状态难以进行分支探索和回滚
- **表达能力受限**: SQL 约束难以表达复杂的跨实体逻辑

#### 实现机制:Typedown Entity + Spec

Monoco 主张将数据从 SQL 数据库迁移到 **Git 仓库中的 Typedown Entity Block**,通过版本控制和符号约束实现更强的状态不变性。

**Typedown 的三层约束体系**:

1. **字段类型约束(L0)**: Pydantic 模型定义

   ````t y pe do w n
   ```model:User
   class User(BaseModel):
       name: str
       role: Literal["admin", "member"]
       mfa_enabled: bool = False
   ```
   ````

2. **模型验证器(L1)**: 自足的一致性检查

   ````typedown
   ```model:Book
   class Book(BaseModel):
       price: float = Field(gt=0)
       discount_price: float = Field(gt=0)

       @model_validator(mode='after')
       def check_discount(self):
           assert self.discount_price <= self.price, \
               "折扣价不能高于原价"
           return self
   ```
   ````

3. **全局规格(L2)**: 跨实体的图级别验证
   ````typedown
   ```spec:check_admin_mfa
   @target(type="User", scope="local")
   def check_admin_mfa(subject: User):
       if subject.role == "admin":
           assert subject.mfa_enabled, \
               f"管理员 {subject.name} 必须开启 MFA"
   ```
   ````

**高级约束示例:全局聚合规则**

````typedown
```spec:check_total_inventory_cap
@target(type="Item", scope="global")
def check_total_inventory_cap(subject):
    # 使用 DuckDB 进行全域查询
    result = sql("SELECT sum(weight) as total FROM Item")
    total_weight = result[0]['total']

    limit = 10000
    assert total_weight <= limit, \
        f"总库存重量 {total_weight} 超过上限 {limit}"

    # 精确归因:仅标记超重实体
    overweight = sql("SELECT id, weight FROM Item WHERE weight > 500")
    for item in overweight:
        blame(item['id'], f"单项重量 {item['weight']} 超过警戒线")
```
````

#### 系统状态不变性的革命性优势

相比传统 CRUD 系统中枚举的不完善逻辑护栏,Typedown 模式具有以下优势:

1. **版本控制即审计日志**
   - 所有状态变更都通过 Git Commit 记录
   - 支持分支探索:可以在 Feature 分支中尝试不同的业务规则
   - 回滚成本极低:只需 `git revert`

2. **多维度业务逻辑约束**
   - **类型层**: Pydantic 的严格类型系统
   - **验证层**: `@field_validator` 和 `@model_validator`
   - **图层**: `spec` 块的全局查询能力(SQL + blame)

3. **护栏强度远超传统系统**
   - **编译时检查**: Typedown 在编译阶段就能发现约束违反
   - **双向诊断**: 错误同时标记在规则定义处和数据定义处
   - **零运行时成本**: 约束在部署前已验证,生产环境无需重复检查

4. **智能体友好**
   - **声明式**: 约束以自然语言 + 代码的形式存在于 Markdown 中
   - **可解释**: LLM 可以直接理解 `spec` 块的语义
   - **可生成**: 智能体可以根据需求自动生成新的约束规则

#### 实际应用场景

**场景 1:ERP 系统的财务规则**

传统方式:

```sql
-- 分散在多个触发器和存储过程中
CREATE TRIGGER check_budget BEFORE INSERT ON expenses ...
CREATE TRIGGER check_approval BEFORE UPDATE ON expenses ...
```

Typedown 方式:

````typedown
```spec:financial_governance
@target(type="ExpenseItem", scope="global")
def check_budget_compliance(subject):
    # 按项目聚合费用
    result = sql("""
        SELECT project_id, sum(amount) as total
        FROM ExpenseItem
        GROUP BY project_id
    """)

    for row in result:
        project = query(row['project_id'])
        if row['total'] > project.budget:
            # 精确归因到超支的费用项
            overbudget = sql(f"""
                SELECT id FROM ExpenseItem
                WHERE project_id = '{row['project_id']}'
            """)
            for item in overbudget:
                blame(item['id'],
                    f"项目 {row['project_id']} 超支")
```
````

**场景 2:Monoco 自身的 Domain Governance**

```python
# monoco/features/issue/linter.py
# FEAT-0136: 项目级域治理检查
num_issues = len(all_issue_metas)
num_epics = len([i for i in all_issue_metas if i.type == "epic"])
is_large_scale = num_issues > 128 or num_epics > 32

if is_large_scale and num_epics > 0:
    untracked_ratio = len(untracked_epics) / len(epics)

    # 规则:未追踪 Epic / 总 Epic <= 25%
    if untracked_ratio > 0.25:
        diagnostics.append(Diagnostic(
            message=f"Domain Governance: 覆盖率过低 "
                   f"({len(untracked_epics)}/{len(epics)} Epics 未追踪). "
                   f"至少 75% 的 Epic 必须分配域.",
            severity=DiagnosticSeverity.Error,
        ))
```

## 3. 三种不变性的协同作用

三种不变性形成了一个完整的质量保障体系:

```
┌─────────────────────────────────────────────────────────┐
│                   系统状态不变性                          │
│              (Typedown Entity + Spec)                   │
│         业务逻辑约束 · 全局一致性 · 版本控制              │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │
┌─────────────────────────────────────────────────────────┐
│                   代码产物不变性                          │
│           (Git Hooks + pytest + ruff + Linter)          │
│         语法正确性 · 风格一致性 · 结构完整性              │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │
┌─────────────────────────────────────────────────────────┐
│                   开发流程不变性                          │
│              (Issue Lifecycle Hooks)                    │
│         工作流规范 · 质量门禁 · 协作协议                  │
└─────────────────────────────────────────────────────────┘
```

**协同机制**:

1. **流程层**确保智能体遵循正确的工作流程(如先 `start` 再 `submit`)
2. **产物层**确保每次提交的代码都通过静态分析和测试
3. **状态层**确保系统的业务逻辑约束在任何分支、任何时刻都得到满足

## 4. 实时监控与强制闭环

体系不变量的执行不是依靠事后的审计,而是通过"准入控制"(Admission Control)机制实现的:

- **Pre-action Hooks**: 在智能体试图开始一个行动之前,检查基础不变量
- **Post-action Hooks**: 在行动完成后,立即验证该操作是否导致了不变量违反
- **Git Pre-commit Hooks**: 在代码提交前执行强制性检查
- **Typedown Compiler**: 在文档编译时验证所有约束

这种实时闭环的监控机制赋予了系统一种"自我保护"的本能。一旦智能体执行了导致不变量失败的操作,系统会立即捕捉到这一"系统级回归",并强制要求智能体进行回滚或立即修复。这一过程发生在任务交付给人类之前,确保了人类所见到的系统永远处于一个合法的、逻辑自洽的状态。

## 5. 关键原则

1. **客观且明确**: 不变量应当是可自动验证的,任何模糊的、需要主观判断的标准都不应作为体系不变量
2. **分层防御**: 通过流程、产物、状态三层不变性构建纵深防御体系
3. **版本控制优先**: 将状态数据纳入 Git 管理,享受分支探索和审计日志的优势
4. **符号约束优于运行时检查**: Typedown 的编译时验证比传统数据库约束更早发现问题
5. **智能体可理解**: 约束以声明式的自然语言 + 代码形式存在,便于 LLM 理解和生成

智能体系统通过这一套冰冷的、不可逾越的规则,建立起了一种机器级的技术诚信。
