# Monoco Issue 查询语法规范

Monoco Issue System (Web & CLI) 采用统一的、语义化的查询语法，让用户能够通过直观的关键词组合实现精确过滤。

## 1. 基础语法 (Basic Syntax)

查询的最基本单元是**词条 (Term)**。我们区分了“可选”与“必选”两种语义。

### 可选项 (Nice to Have)

这些词条**不是必须**的，但如果存在，会提高相关性或作为候选项。

- **语法**: `keyword` (直接输入)
- **语义**: **Should Include**。
- **示例**:
  - `login`: 倾向于查找包含 "login" 的 Issue。

### 必选项 (Must Include)

目标**必须包含**指定的关键词。

- **语法**: `+keyword` (加号前缀)
- **语义**: **Must Include**。
- **示例**:
  - `+bug`: 结果中**必须**包含 "bug"。

### 排除项 (Excludes)

目标**必须不包含**指定的关键词。

- **语法**: `-keyword` (减号前缀)
- **语义**: **Must Not Include**。
- **示例**:
  - `-ui`: 排除包含 "ui" 的 Issue。

## 2. 短语查询 (Phrases)

如果一个查询词条内部**包含空格**，则必须使用**双引号**将整个短语包裹起来。

- **语法**: `"phrase with space"`
- **示例**:
  - `"login error"` -> 视为一个普通的 Nice to Have 短语。
  - `+"critical error"` -> 视为一个 Must Include 短语。

## 3. 组合逻辑 (Combination)

多个词条之间通过空格分隔。逻辑优先级如下：

1. **排除项 (-)** 优先级最高：任何匹配排除项的 Issue 直接被过滤。
2. **必选项 (+)** 必须全部满足 (Implicit AND)。
3. **可选项** (无前缀)：
   - 如果存在必选项：可选项仅影响排序或额外信息匹配。
   - 如果**不存在**必选项：则至少需要满足一个可选项 (Implicit OR)（注：具体实现可能视场景微调为全匹配）。

**常见组合示例**:

- `+bug -ui login`
  - 必须包含 `bug`
  - 必须不含 `ui`
  - `login` 是加分项（优先显示 login 相关的 bug）

## 4. 搜索范围与规则 (Scope & Rules)

### 规则

- **忽略大小写 (Case Insensitive)**: `Bug`, `BUG`, `bug` 被视为相同。
- **全域搜索 (Full Scope)**: 并在一次查询中匹配所有元数据和内容。

### 匹配字段

| 字段             | 说明                                     |
| :--------------- | :--------------------------------------- |
| **ID**           | 如 `FEAT-0012`                           |
| **Title**        | 标题文本                                 |
| **Body**         | 正文内容                                 |
| **Status**       | 状态 (`open`, `closed`, `backlog`)       |
| **Stage**        | 阶段 (`todo`, `doing`, `review`, `done`) |
| **Type**         | 类型 (`epic`, `feature`, `chore`, `fix`) |
| **Tags**         | 标签列表                                 |
| **Dependencies** | 依赖项 ID                                |
