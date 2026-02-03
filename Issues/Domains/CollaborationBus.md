# CollaborationBus

## 定义
协作总线 - 负责人与 Agent、Agent 与 Agent 之间信息传递与协作的通用通道。它是人机协作的"神经系统"，承载工作流可视化、即时通讯、反馈收集与演化信号传递。

## 职责
- **Interface Layer**: 提供人机交互的多元界面
  - **Kanban**: 可视化工作流与任务看板
  - **IDE Extension**: 编辑器内集成界面
  - **CLI/Web UI**: 命令行与网页交互界面
  - **IM Integration**: 钉钉、飞书等即时通讯平台集成
- **Message Passing**: 异步消息传递机制
  - **Memo**: 快速笔记与想法捕捉
  - **Notification**: 系统通知与提醒
  - **Event Broadcasting**: 事件广播与订阅
- **Feedback Collection**: 双向反馈收集
- **Evolution Signaling**: 演化方向信号传递

## 边界
- **负责**: 信息如何传递、如何呈现、如何收集
- **不负责**: 
  - 工作项本身的管理（IssueSystem/IssueGovernance）
  - Agent 如何执行任务（AgentEmpowerment/AgentScheduling）
  - 工具的具体实现（DevEx）
  - 运行时基础设施（Foundation/Infrastructure）

## 原则
- **Unified Channel**: 统一通道，避免信息孤岛
- **Async by Default**: 默认异步，支持同步 when necessary
- **Context Preserved**: 信息传递保留完整上下文
