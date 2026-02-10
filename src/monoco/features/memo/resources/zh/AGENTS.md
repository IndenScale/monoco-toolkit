## 信号队列模型

轻量级笔记，用于快速记录想法。

- **Memo 是信号，不是资产** - 其价值在于触发行动
- **文件存在 = 信号待处理** - Inbox 有未处理的 memo
- **文件清空 = 信号已消费** - Memo 在处理后被删除
- **Git 是档案** - 历史记录在 git 中，不在应用状态里

## 命令

- **添加**: `monoco memo add "内容" [-c 上下文]` - 创建信号
- **列表**: `monoco memo list` - 显示待处理信号（已消费的 memo 在 git 历史中）
- **删除**: `monoco memo delete <id>` - 手动删除（通常自动消费）
- **打开**: `monoco memo open` - 直接编辑 inbox

## 工作流

1. 将想法捕获为 memo
2. 当阈值（5个）达到时，自动触发 Architect
3. Memo 被消费（删除）并嵌入 Architect 的 prompt
4. Architect 从 memo 创建 Issue
5. 不需要"链接"或"解决" memo - 消费后即消失

## 指南

- 使用 Memo 记录** fleeting 想法** - 可能成为 Issue 的事情
- 使用 Issue 进行**可操作的工作** - 结构化、可跟踪、有生命周期
- 永远不要手动将 memo 链接到 Issue - 如果重要，创建一个 Issue
