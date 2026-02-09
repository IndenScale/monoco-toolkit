# Agent Harness: 从阻止到赋能的连续光谱

> 信号类型: 架构概念澄清
> 创建: 2026-02-09
> 状态: 待处理 (待转化为 Issue 或设计文档)

---

## 核心洞察

Agent Harness 不是 Braintrust 定义的 "Evaluation Harness"（后置统计评估），而是**过程信号系统**——通过 pre/post-event hooks 在行为发生时实时干预。

```
控制力度光谱

Blocking ◄──────────────────────────────────────► Aiding
  阻拦              控制              提示              帮助
   │                │                │                │
   ▼                ▼                ▼                ▼
┌─────┐        ┌─────┐        ┌─────┐        ┌─────┐
│ 拒绝 │   →    │ 限制 │   →    │ 提醒 │   →    │ 建议 │
│ 操作 │        │ 选项 │        │ 风险 │        │ 最佳 │
│      │        │      │        │      │        │ 实践 │
└─────┘        └─────┘        └─────┘        └─────┘
   │                │                │                │
pre-event      pre-event       pre-event       post-event
 (hard)         (soft)          (info)          (guide)
```

---

## 统一挂载点: Pre/Post Event Hooks

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Action                         │
│                                                         │
│  pre-hook ──► [ 核心行为 ] ──► post-hook                │
│      │                            │                     │
│      ▼                            ▼                     │
│  ┌─────────┐                ┌─────────┐                 │
│  │  阻拦    │                │  复盘    │                 │
│  │  控制    │                │  提示    │                 │
│  │  校验    │                │  建议    │                 │
│  └─────────┘                └─────────┘                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 实例: `monoco issue submit`

| 控制力度 | Hook 类型 | 具体行为 |
|:---------|:----------|:---------|
| **阻拦** | pre-submit | checklist 未完成 → 阻断提交 |
| **控制** | pre-submit | 自动添加测试标签 |
| **提示** | pre-submit | "此变更涉及 5 个文件，建议分步提交" |
| **帮助** | post-submit | "请检查测试用例是否覆盖新特性" |
| **帮助** | post-submit | "建议填写 review comment 说明变更原因" |

---

## 关键特征

1. **可执行的最佳实践**
   - 传统: 文档写着"提交前要检查测试用例"
   - Harness: 未完成 → 阻断 + 提示"请添加测试用例"

2. **隐性知识编码**
   - 将团队经验转化为自动化信号
   - 减少人工 prompting 的必要性

3. **可组合性**
   ```
   pre-submit: [check_checklist, check_tests, warn_big_diff]
   post-submit: [suggest_review_template, auto_link_issue]
   ```

---

## 与现有概念的区别

| 概念 | 本质 | 关系 |
|:-----|:-----|:-----|
| Braintrust Evaluation Harness | 后置统计评估 | ❌ 不同 |
| Linter/静态检查 | 规则匹配 | ⚠️ 子集（仅阻拦端）|
| **Your Agent Harness** | 过程信号光谱 | ✅ 完整定义 |

---

## 待解决问题

1. **标准化 hook 协议**? (`monoco.hooks.pre-submit`)
2. **Harness 注册表**? (可共享、可组合的 hooks)
3. **内置 vs 自定义**? (monoco 提供 vs 项目级 `.monoco/hooks/`)

---

## 可能去向

- [ ] 转化为 FEAT Issue: 设计 Agent Harness 协议
- [ ] 转化为设计文档: `docs/agent-harness.md`
- [ ] 集成到 Monoco CLI: 实现 hook 系统
- [ ] 关闭: 概念已澄清，无需进一步行动
