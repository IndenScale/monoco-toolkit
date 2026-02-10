# Ralph Loop - 会话接力系统

## 核心概念

Ralph Loop 是 Monoco 的长程任务执行协议。它通过**会话接力**机制，让单个 Agent 能够突破上下文窗口限制，完成复杂任务。

### 为什么需要接力？

1. **上下文腐烂** - 长会话导致推理质量指数级下降
2. **失败模式陷阱** - 错误假设在会话中固化，难以跳出
3. **关注点分离** - 每个会话只需关注当前里程碑的增量工作

## 两角色架构

```
┌─────────────────────────────────────────┐
│  执行者 (Executor)                       │
│  Plan → Implement → Test → Submit       │
│       ↓ 自我接力（按需）                  │
│  RALPH.md → 新 Session → 继续           │
└─────────────────────────────────────────┘
                    ↓ submit
┌─────────────────────────────────────────┐
│  审查者 (Reviewer) - 独立视角            │
│  Verify → Challenge → Decide            │
│  (不可替代，双防御系统)                   │
└─────────────────────────────────────────┘
```

**关键原则**：
- Executor 可以自我接力多次，直到任务完成
- Reviewer 只在 `issue submit` 时介入，提供独立审查
- Plan-Implement 连续性由 Executor 自主维护

## RALPH.md - 交接文档

当 Executor 检测到以下情况时，生成 RALPH.md：

1. **上下文极限** - 感知到推理质量下降
2. **超时中断** - 需要暂停但任务未完成
3. **错误恢复** - 陷入失败模式，需要新鲜上下文

### 文档结构

```markdown
# RALPH.md

## 元数据
- Issue: FEAT-XXX
- Session: sess_xxx
- 停止原因: context_limit / timeout / user_interrupt

## 当前状态
- Stage: implementing
- 正在处理: src/xxx.py 第 200 行

## 已完成
- [x] 分析现有架构
- [x] 设计新模型

## 待办
- [ ] 实现核心函数
- [ ] 编写测试

## 关键决策
1. 决定保留 EventBus，但简化事件类型
2. 决定移除 Planner 触发

## 下一步（继任者必读）
1. 完成 ExecutionHandler._should_handle()
2. 更新测试用例
3. 运行 pytest 验证

## 警告
⚠️ 不要删除 MemoThresholdHandler 的测试
```

## Stop Hooks 机制

Claude Code 在会话结束时触发：

```
用户停止 / 超时
    ↓
Stop Hook: monoco hook on-stop
    ↓
Agent 自检：
    - Issue 完成了吗？→ 直接退出
    - 需要接力吗？→ 生成 RALPH.md
    - 还能继续吗？→ 请求延长
    ↓
安排继任 Session（如需要）
```

## 命令

```bash
# 手动准备交接（当前 Session 自知极限将至）
monoco relay prepare

# 查看接力状态
monoco relay status FEAT-XXX

# 手动恢复接力
monoco relay resume FEAT-XXX

# 清理接力状态
monoco relay clear FEAT-XXX
```

## Agent 行为准则

### 作为 Executor

1. **自主判断** - 当感到"思维混乱"时，主动生成交接文档
2. **最小交接** - 只交接必要信息，保持文档简洁
3. **明确下一步** - 为继任者提供清晰的操作指引

### 作为继任者

1. **先读 RALPH.md** - 启动时优先读取交接文档
2. **验证状态** - 检查 Issue 文件和代码现状
3. **继续推进** - 专注于当前里程碑的增量工作

## 与 Ralph Loop 理论的对齐

- **Loop** - 每个 Session 是一次执行尝试
- **Relay** - RALPH.md 实现跨 Session 状态传递
- **Post-mortem** - 选择性生成，用于错误恢复
