# ADR-002: Lint 错误收集与展示策略

## 状态

**Proposed** - 待评审

## 背景

当前 `monoco issue lint` 的行为存在以下问题：

1. **解析层中断**：如果 Front Matter YAML 解析失败，会抛出异常导致整个 lint 过程中断，无法检查其他规则（如状态一致性、引用完整性等）
2. **错误信息过载**：当 Issue 存在多个问题时，一次性展示所有 diagnostics 可能导致 Agent/用户难以快速定位关键问题
3. **缺乏优先级引导**：Agent 无法区分"致命错误"和"建议性警告"，不知道应该先修复什么

## 决策

### 1. 全量收集策略（Fail-Soft）

**原则**：Lint 应该尽可能跑完所有校验项，收集所有 diagnostic，不因单个校验失败而中断。

```python
# 当前问题：解析失败会中断
def validate_issue(content: str) -> List[Diagnostic]:
    diagnostics = []
    
    # 问题1：如果 YAML 解析失败，整个函数抛出异常
    meta = parse_frontmatter(content)  # 可能抛出 yaml.YAMLError
    
    # 下面的检查永远不会执行
    diagnostics.extend(validate_state_matrix(meta))
    diagnostics.extend(validate_references(meta))
    ...

# 改进后：失败时添加 diagnostic 并继续
def validate_issue(content: str) -> List[Diagnostic]:
    diagnostics = []
    meta = None
    
    # 1. 尝试解析 Front Matter
    try:
        meta = parse_frontmatter(content)
    except yaml.YAMLError as e:
        diagnostics.append(Diagnostic(
            severity=Fatal,
            message=f"Front Matter 解析失败: {e}"
        ))
        # 继续：尝试用正则提取基本信息进行后续检查
        meta = extract_partial_meta(content)
    
    # 2. 即使 meta 不完整，也尝试运行其他检查
    if meta:
        diagnostics.extend(validate_state_matrix(meta))
        diagnostics.extend(validate_references(meta))
        ...
    
    return diagnostics
```

### 2. 分层展示策略

收集所有 diagnostics 后，按以下优先级分层展示：

| 层级 | Severity | 说明 | 默认展示数量 |
|------|----------|------|-------------|
| Fatal | Error (Critical) | 阻止命令执行的错误（如 YAML 解析失败） | 全部 |
| Error | Error | 数据完整性错误（如状态不匹配） | 前 3 个 |
| Warning | Warning | 建议性警告（如缺少 review comments） | 前 2 个 |

**默认行为**：
- 终端模式：展示所有 Error，前 5 个 Warning
- Agent 模式（JSON）：返回全部 diagnostics，但添加 `prioritized` 标记前 5 个

```json
{
  "diagnostics": [
    {"severity": "error", "message": "...", "line": 10},
    {"severity": "error", "message": "...", "line": 23},
    ...
  ],
  "summary": {
    "total": 12,
    "fatal": 1,
    "errors": 5,
    "warnings": 6
  },
  "prioritized": [0, 1, 2, 3, 4],  // 需要优先处理的问题索引
  "suggestions": [
    "首先修复 Front Matter 解析错误",
    "然后检查状态一致性",
    "..."
  ]
}
```

### 3. 渐进式修复建议

为 Agent 提供结构化的修复路径：

```python
class LintResult:
    diagnostics: List[Diagnostic]
    
    # 按优先级排序的建议修复顺序
    fix_order: List[FixSuggestion]
    
    # 是否可以自动修复
    auto_fixable: bool
    
    # 修复后需要重新检查的项目
    recheck_items: List[str]

@dataclass
class FixSuggestion:
    priority: int
    description: str
    command: Optional[str]  # 如："monoco issue lint FEAT-0123 --fix"
    manual_steps: List[str]  # 需要手动执行的步骤
```

## 示例场景

### 场景 1：Front Matter 解析失败

**输入**：YAML 格式错误的 Issue 文件

**当前行为**：
```
Error: Invalid YAML in front matter: mapping values are not allowed here
# 直接退出，不检查其他规则
```

**改进后行为**：
```
[Fatal] Front Matter 解析失败: line 12, column 5
[Error] State Mismatch: status='closed' 但文件在 open/ 目录 (line 8)
[Warning] Missing Review Comments section (line 45)

建议修复顺序：
1. 修复 YAML 语法错误 (line 12)
2. 移动文件到正确目录，或修改 status
3. 添加 Review Comments 章节
```

### 场景 2：多个错误同时存在

**输入**：submit 前的 Issue 有多处未完成

**改进后输出**（Agent 模式）：
```json
{
  "diagnostics": [
    {"severity": "error", "line": 23, "message": "Uncheck item: 'Implement API'"},
    {"severity": "error", "line": 25, "message": "Uncheck item: 'Add tests'"},
    {"severity": "error", "line": 45, "message": "Missing solution field for closed issue"},
    {"severity": "warning", "line": 50, "message": "Review Comments section empty"},
    {"severity": "warning", "line": 10, "message": "Domain not assigned"}
  ],
  "prioritized": [0, 1, 2],  // 优先修复前 3 个 Error
  "summary": {
    "blocking": 3,  // 阻止 submit 的错误数
    "total": 5
  },
  "next_action": "完成 Technical Tasks 列表中的未勾选项目"
}
```

## 后果

### 正面影响

1. **更好的 Agent 体验**：Agent 获得完整的错误图谱，可以制定修复策略
2. **渐进式修复**：用户可以分步修复，不必一次解决所有问题
3. **调试效率**：即使 Front Matter 损坏，仍能检查其他问题

### 负面影响

1. **复杂度增加**：需要处理部分解析失败后的降级检查
2. **可能产生误报**：Front Matter 解析失败后，基于部分数据的检查可能不准确

### 风险缓解

- **降级标记**：基于不完整数据的 diagnostic 添加 `[Partial Data]` 标记
- **可配置性**：提供 `--strict` 模式，遇到 Fatal 错误立即退出（CI 场景）

## 替代方案

### 方案 A：保持当前行为（拒绝）

第一个 Fatal 错误立即退出。

**拒绝原因**：
- Agent 无法获得完整上下文
- 修复效率低（需要多次运行 lint）

### 方案 B：按文件分组中断（拒绝）

单个文件遇到 Fatal 错误跳过该文件，继续检查其他文件。

**拒绝原因**：
- 无法解决单文件多错误的问题
- 不符合 Issue Lint 的主要使用场景（单文件深度检查）

## 实现计划

### Phase 1: 错误收集改进
1. 修改 `parse_issue` 支持 `fail_soft` 模式
2. 添加 `extract_partial_meta` 函数从损坏的 YAML 中提取基本信息
3. 确保所有 `validate_*` 函数能处理部分数据

### Phase 2: 结果排序与展示
1. 实现 diagnostic 优先级排序（Fatal > Error > Warning）
2. 添加 `--max-errors` 和 `--max-warnings` 参数
3. Agent 模式输出添加 `prioritized` 和 `summary` 字段

### Phase 3: 修复建议
1. 为常见错误添加 `FixSuggestion`
2. 实现 `lint --fix` 的渐进式修复（先修复 Fatal，再 Error）

## 参考

- [Issue Validator 实现](../../../monoco/features/issue/validator.py)
- [Linter 实现](../../../monoco/features/issue/linter.py)
- [Lint 命令](../../../monoco/features/issue/commands.py)

## 记录

- **提出**: 2026-02-05
- **作者**: @indenscale
- **相关 Issue**: FEAT-0180（相关）
