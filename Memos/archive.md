# Monoco Memos Archive

## [844f87] 2026-02-01 21:14:28

- **Status**: [x] Processed (CHORE-0037, FIX-0001)

> **Context**: `Post-Mortem`

复盘记录：

1. [Critical] 蜂群风暴：Daemon 调度器 Handover 策略引发无限 Agent 进程增殖，导致 OOM 崩溃。需增加冷却/退避机制。
2. [Docs] Context 缺失： 未说明 Memo 存储位置 ()，导致 Agent 无法正确定位文件。

## [325b48] 2026-02-01 21:35:48

- **Status**: [x] Processed (FEAT-0167)

> **Context**: `UX Feedback`

用户反馈：Issue 生命周期中的 'solution' 字段定义模糊。CLI 报错 'requires solution implemented' 但 issue update 命令并不支持 --solution 参数，导致通过命令行闭环困难。应明确它属 Front Matter 还是正文。

## [0c262b] 2026-02-01 21:37:06

- **Status**: [x] Processed (FEAT-0167)

> **Context**: `DevEx`

缺陷反馈：

1. [Template] 生成的 Markdown 模版 Front Matter 中缺失 字段默认值（应为 或占位），导致验证逻辑依赖隐式行为。
2. [CLI] 缺乏 参数接口，无法在不编辑文件的情况下满足 Close Policy (Requires solution='implemented')。
   影响：阻碍了 Agent 通过纯 CLI 指令完成 Issue 闭环。

## [68eb0d] 2026-02-01 21:40:17

- **Status**: [x] Processed (FIX-0010)
- **Context**: `i18n`

i18n语言检测阈值优化建议：当前 detect_language 函数使用 5% CJK 字符阈值判断中文内容，但对于技术文档类 Issue（大量英文术语、代码），容易被误判为英文。建议：1) 对于 Issue 文件放宽阈值或跳过检测；2) 或增加对技术文档的特殊处理，识别技术术语不计入语言检测

## [e691f9] 2026-02-02 08:56:58

- **Status**: [x] Processed (FEAT-0151, FEAT-0153, FEAT-0152)

> **Context**: `Arch Decision`

Artifacts & Mailroom 架构决策复盘：

1. [Mindset] 拒绝过度工程。去 GPU/MinerU，转向『截图降维 + 远程 VLM API』的轻量化路线。
2. [TechStack] 确定 Office -> PDF (LibreOffice) -> WebP (PyMuPDF, 150 DPI) 链路。调查证实 kimi-cli 原生支持 WebP。
3. [Storage] 混合存储架构：全局物理 CAS 池 (~/.monoco/artifacts) 实现内容寻址去重 + 项目级逻辑 Symlink 满足自包含与 Generative UI 扩展。
4. [Workflow] 遵循『基建先行 -> 技能赋能 -> 自动化实现』。拆分为 0151(Core), 0152(Skills), 0153(Auto) 三个 Feature 闭环。

## [b3143c] 2026-02-02 20:42:40
- **Status**: [x] Processed (FIX-0011)
- **Context**: `workflow`

monoco issue close 检查的是 main 分支上的 Issue 状态，但应该读取 dev branch 的 Issue ticket 状态。这导致在 feature branch 上完成工作后，回到 main 分支无法正确 close issue。影响自动 cherry-pick 工作流的价值。

## [673948] 2026-02-03 01:40:17
- **Status**: [x] Processed (FEAT-0168)
- **Context**: `architecture`

架构讨论: IM 协作模式与存储方案 (2026-02-03)

## 参与
- 人类架构师
- Agent (Kimi CLI)

## 核心结论

### 1. Architect 双重职责设计 ✅
Architect 统一处理 Memo Inbox + IM Inbox 是正确的。
单一入口简化逻辑，Architect 具备需求分析能力。

### 2. 非交互式确认机制 ✅
人类不需要点击按钮，而是发送带 Proposal ID 的消息来确认。
Architect 识别到自己上一轮的产物 → 自动放行 → 创建 Issue。
符合 Filesystem as API 哲学。

### 3. 三种协作模式
- 模式 A (Quick): User → IM → Architect → outbox/ → IM Reply (无 Issue)
- 模式 B (Proposal): User → IM → Architect → Proposal → 用户确认消息 → Issues/
- 模式 C (Autopilot): Issue doing → Engineer → PR → Reviewer → 确认消息 → 合并

### 4. 存储方案决策
- 文件系统优先 (Filesystem as API)
- 延迟引入数据库直到明确痛点
- 索引层作为性能优化手段 (可重建)
- 监控文件数量，>100k 时考虑 SQLite

## 待办
- [ ] 创建 FEAT Issue 实现 Proposal 机制
- [ ] 定义 IMMessage 和 Proposal JSON Schema
- [ ] 实现 .monoco/im/ 目录结构

## 参考
- EPIC-0032: Collaboration Bus
- EPIC-0033: IM 集成
- FEAT-0160: IM 核心消息闭环
- FEAT-0161: IM 多模态附件处理

## [81b0f8] 2026-02-03 20:43:28
- **Status**: [x] Processed (CHORE-0038)
- **Context**: `git-workflow`

跨分支 commit 污染记录:

现象: 在 FEAT-0166 开发过程中，发现 main 分支上存在本应在 feature 分支的 commit

具体表现:
- main 分支存在 f9fe028 'chore(issue): doing FEAT-0166' commit
- 这导致执行 monoco issue close 时出现 'Issue found in multiple branches' 错误
- 同时 FIX-0009 的 commit 也混入了 FEAT-0166 分支 (efb08d0, 95b5cb2 等)

影响:
1. Issue 状态同步混乱
2. 无法直接执行 monoco issue close
3. 分支隔离被破坏

建议:
- 严格遵循 '禁止在 main/master 分支直接修改代码' 的规则
- 切换分支前先检查当前工作区状态
- 考虑添加更强的 pre-checkout hook 保护
