# 02. 承诺升级（Ascending Milestone）

## 1. 任务生命周期中的熵减过程

在处理长程复杂任务时，智能体系统面临的核心挑战是"状态漂移"（State Drift）。随着执行步骤的累积，如果缺乏结构化的质量门禁，系统对任务完成状态的确定性会随着信息熵的增加而迅速衰减。这种衰减表现为：任务目标模糊化、变更范围失控、验收标准缺失、以及执行产物与初始承诺的偏离。

为了对抗这种自然倾向，Monoco 引入了"承诺升级"（Ascending Milestone）机制。该机制将任务的宏观生命周期拆分为一系列单向不可逆的逻辑阶段（Stage），每个阶段的转换都需要通过显式的质量验证。这种设计的核心在于：**通过强制性的行政手续和技术检查，将抽象的"任务进度"转化为可验证的物理状态**。

在 Monoco 的实现中，这种承诺通过 `IssueStage` 枚举的显式迁移来表达：`draft` → `doing` → `review` → `done`。每次 Stage 转换都会触发相应的生命周期钩子（Lifecycle Hooks）和验证器（Validator），确保任务在进入下一阶段前已满足当前阶段的所有准出条件。随着 Stage 的推进，系统对任务的承诺强度与不可逆转性递增，最终在 `done` 阶段完成物理合并（Merge to Trunk），使变更成为系统真理的一部分。

## 2. Monoco 的 Stage 实现：承诺梯度与质量门禁

Monoco 通过 `IssueStage` 枚举定义了四个核心阶段，每个阶段都配备了相应的命令（Command）、钩子（Hook）和验证器（Validator）来强制执行质量门禁。

### 2.1 规划阶段（stage: draft）

**触发命令**: `monoco issue open <id>`

**系统期待**:

- **叙事嵌入**: 任务必须通过 `parent` 字段显式引用一个更高层级的 `EPIC` 或父级任务。这确保了当前的原子操作不是孤立的，而是被纳入了更广泛的"系统演化叙事"中。
  - **技术实现**: `IssueMetadata.validate_lifecycle()` 在模型层强制验证非 EPIC 类型的 Issue 必须有 `parent` 字段。
- **元数据完备性**: 必须准确填写 `domains`（领域归属）和 `criticality`（严重程度）。
  - **技术实现**: `IssueValidator._validate_domains()` 检查 domain 的有效性和治理规则。

**质量门禁**: 在此阶段，系统对任务目标进行第一次状态锁定。`post-issue-create` 钩子会立即运行 Lint 检查，向智能体反馈缺失的必填字段。

### 2.2 执行阶段（stage: doing）

**触发命令**: `monoco issue start <id> [--branch]`

**系统期待**:

- **隔离环境创建**: 默认情况下，系统会创建一个独立的 Git 分支（`feat/<id>-<slug>`）或 Worktree，确保变更不会污染主干（Trunk）。
  - **技术实现**: `core.start_issue_isolation()` 创建隔离环境，并将 `isolation.ref` 和 `isolation.type` 记录到 Issue 元数据中。
- **任务结构定义**: 必须在 Issue 正文中定义至少一个 Technical Task（技术任务）。
  - **技术实现**: `IssueValidator._validate_state_requirements()` 检查 `doing` 阶段是否存在 Technical Tasks 章节，如果缺失则报告 WARNING。
- **资源声明**: 智能体在执行过程中，应通过 `monoco issue sync-files` 维护 `files` 列表，声明其变更的"影响半径"。

**质量门禁**: `pre-issue-start` 钩子会验证当前是否在 Trunk 分支上（避免嵌套分支）。`post-issue-start` 钩子会提供下一步操作建议。

### 2.3 验证阶段（stage: review）

**触发命令**: `monoco issue submit <id>`

**系统期待**:

- **Technical Tasks 完成**: 所有 Technical Tasks 必须标记为已完成（`[x]`）、已取消（`[~]`）或已合并（`[+]`）。不允许存在待办（`[ ]`）或进行中（`[-]`、`[/]`）的任务。
  - **技术实现**: `IssueValidator._validate_state_requirements()` 在 `review` 阶段强制检查 Technical Tasks 的完成状态，未完成的任务会触发 ERROR 级别的诊断。
- **Review Comments 章节**: 必须存在非空的 `## Review Comments` 章节，记录评审反馈或自我复盘。
  - **技术实现**: `IssueValidator._validate_structure_blocks()` 检查 `review` 阶段是否有 Review Comments 章节及其内容，缺失或为空会触发 ERROR。
- **占位符清除**: 所有模板占位符（如 `<!-- TODO: ... -->`）必须被替换为实质性内容。
  - **技术实现**: `IssueValidator._validate_placeholders()` 在 `review` 阶段将未清除的占位符视为 ERROR（其他阶段为 WARNING）。
- **文件同步与 Lint 验证**: 系统会自动同步 `files` 列表并运行完整的 Lint 检查。
  - **技术实现**: `pre-issue-submit` 钩子自动调用 `sync_issue_files()` 和 `check_integrity()`，如果存在 Lint 错误则阻止提交（DENY）。

**质量门禁**: `pre-issue-submit` 是最严格的质量门禁，任何 Lint 错误都会阻止 Stage 转换。`post-issue-submit` 钩子会生成 Delivery Report，汇总变更产物。

### 2.4 合并阶段（stage: done）

**触发命令**: `monoco issue close <id> --solution <implemented|cancelled|...>`

**系统期待**:

- **Acceptance Criteria 验证**: 所有 Acceptance Criteria（验收准则）必须标记为已验证（`[x]`）。
  - **技术实现**: `IssueValidator._validate_state_requirements()` 在 `done` 阶段强制检查 AC 的完成状态，未通过的 AC 会触发 ERROR。
- **Review Comments 解决**: 所有 Review Comments 中的可操作项必须标记为已解决（`[x]` 或 `[~]`）。
  - **技术实现**: `IssueValidator._validate_state_requirements()` 检查 Review Comments 中的 checkbox 状态，待办或进行中的项会触发 ERROR。
- **Solution 声明**: 必须显式声明 `solution` 类型（`implemented`、`cancelled`、`wontfix`、`duplicate`）。
  - **技术实现**: `IssueMetadata.validate_lifecycle()` 在模型层强制验证 `closed` 状态必须配对 `solution` 字段。
- **物理合并**: 系统会将隔离环境中的变更合并回 Trunk，并清理分支/Worktree。
  - **技术实现**: `move_close()` 命令通过原子事务（Atomic Transaction）执行合并操作，失败时自动回滚。

**质量门禁**: `done` 阶段是承诺的最高强度。所有变更在通过验证后，会通过 `git checkout` 或 `git merge` 的方式合并到 Trunk，成为系统真理的一部分。`pre-issue-close` 和 `post-issue-close` 钩子确保合并过程的完整性。

## 3. "棕色巧克力"条款：防御性手续的哲学

在 Monoco 的设计中，上述这些看似繁琐的文本手续（如替换占位符、勾选 CheckBox、填写 Parent 引用）实际上扮演了类似摇滚乐队合同中"棕色巧克力条款"（Van Halen's Brown M&M's clause）的角色。

在 1980 年代，Van Halen 乐队会在极其详细的演艺合同中埋藏一个看似荒谬的要求：后台提供的 M&M 巧克力中严禁出现棕色的巧克力。这并非出于审美，而是作为一种"金丝雀测试（Canary Test）"：如果承办方忽略了巧克力颜色这种细节，说明他们大概率也没有仔细阅读复杂的舞台电力和结构安全规范。

在智能体系统中，这些"行政手续"是系统对智能体注意力与逻辑自洽性的廉价探测工具：

- **占位符清除检查**：如果一个 Agent 连 `Review Comments` 占位符都未能根据实际任务产物进行替换，那么系统有理由怀疑其生成的内容极有可能包含幻觉或未经深思熟虑。这正是 `IssueValidator._validate_placeholders()` 在 `review` 和 `done` 阶段将未清除占位符视为 ERROR 的原因。
- **Parent 字段验证**：如果 `parent` 字段缺失，说明 Agent 失去了对全局架构坐标的掌控。`IssueMetadata.validate_lifecycle()` 通过模型层验证强制要求非 EPIC 类型的任务必须有父级引用，确保任务不会成为孤立的"电信号"。
- **CheckBox 完成度检查**：Technical Tasks 和 Acceptance Criteria 的 CheckBox 状态不仅是进度统计，更是对 Agent 逻辑覆盖度的显式声明。`IssueValidator._validate_state_requirements()` 通过解析 Markdown 内容块，强制验证不同 Stage 下 CheckBox 的完成状态，确保 Agent 没有跳过关键步骤。

通过这些高频的琐碎要求，系统强制 Agent 在每个阶段进行"行政回头"，检查细节。只有通过了这些"棕色巧克力"测试，系统才会允许该任务进入下一个高能量状态的承诺节点。这种设计的本质是：**用低成本的形式化检查，探测高成本的语义质量问题**。

## 4. 状态持久化与计算连续性

承诺升级机制不仅是质量保证手段，更是系统韧性的保障。通过将每个 `stage` 的迁移状态及上述"手续产物"进行持久化存储，智能体系统实现了"计算的原子性"。

在 Monoco 的实现中，每次 Stage 转换都会触发 Git 提交，将 Issue 文件的状态变更记录到版本历史中。这种设计带来了两个关键优势：

1. **可恢复性（Recoverability）**: 即使算力中断或环境崩溃，新的运行周期可以通过读取当前 `stage` 下的 Issue 状态——包括那些已经勾选的 CheckBox 和已编辑的总结——重新构建完整的执行上下文。Agent 无需从头开始，而是可以从上一个承诺节点继续推进。

2. **可审计性（Auditability）**: 所有 Stage 转换都通过 Git 历史可追溯。`move_close()` 命令在执行合并操作时，会通过原子事务（Atomic Transaction）机制确保：要么所有变更成功合并到 Trunk，要么在失败时完全回滚到初始状态。这种"全有或全无"的语义，使得系统能够在不确定的运行环境中表现出高度的确定性。

这种基于逻辑阶段的状态管理，使得 Monoco 能够支持无限长程的任务推进。每个 Stage 的完成都是一个"检查点"（Checkpoint），系统可以在任意时刻中断并恢复，而不会丢失已经完成的工作。这正是 Ascending Milestone 机制的核心价值：**通过强制性的质量门禁和持久化的状态管理，将不确定的长程任务转化为可验证、可恢复、可审计的确定性过程**。
