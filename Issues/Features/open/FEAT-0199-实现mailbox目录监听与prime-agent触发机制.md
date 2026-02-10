---
id: FEAT-0199
uid: e348c7
type: feature
status: open
stage: doing
title: 实现Mailbox目录监听与Prime Agent触发机制
created_at: '2026-02-10T15:16:49'
updated_at: '2026-02-10T15:17:53'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0199'
files: []
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-10T15:16:49'
---

## FEAT-0199: 实现Mailbox目录监听与Prime Agent触发机制

## Objective
实现完整的Mailbox目录监听机制，当DingTalk等外部消息到达mailbox时，自动触发Prime Agent进行处理。这将实现"监听目录-创建mail到达消息-触发primal agent"的完整自动化工作流，提升Monoco系统的响应能力和自动化水平。

**核心价值**：
1. **自动化响应**：外部消息到达后自动触发Agent处理，无需人工干预
2. **实时处理**：通过目录监听实现毫秒级响应
3. **架构扩展**：为未来支持更多消息源（Email、Slack等）奠定基础
4. **智能路由**：基于消息内容智能调度合适的Agent

## Acceptance Criteria
- [ ] DingTalk消息到达mailbox后，系统自动检测到新文件
- [ ] 触发`MAILBOX_AGENT_TRIGGER`事件并携带消息元数据
- [ ] Prime Agent被正确调度并接收消息上下文
- [ ] 支持防抖机制，避免短时间内频繁触发Agent
- [ ] 提供配置选项：监听目录、轮询间隔、触发条件等
- [ ] 完整的错误处理和日志记录
- [ ] 单元测试覆盖核心功能
- [ ] 集成测试验证端到端工作流

## Technical Tasks
<!-- Status Syntax: -->
<!-- [ ] To Do -->
<!-- [/] Doing -->
<!-- [x] Done -->
<!-- [~] Cancelled -->
<!-- - [ ] Parent Task -->
<!--   - [ ] Sub Task -->

### 1. 架构设计与接口定义
- [ ] 设计MailboxWatcher类架构，继承自`PollingWatcher`
- [ ] 定义MailboxAgentHandler事件处理器接口
- [ ] 设计Prime Agent角色模板和配置
- [ ] 确定与现有EventBus、AgentScheduler的集成方式

### 2. 核心组件实现
- [ ] 实现`MailboxWatcher`：监听`.monoco/mailbox/inbound/`目录
  - [ ] 支持按provider子目录过滤
  - [ ] 实现防抖机制（30秒窗口）
  - [ ] 正确触发`MAILBOX_AGENT_TRIGGER`事件
- [ ] 实现`MailboxAgentHandler`：处理mailbox事件
  - [ ] 订阅`MAILBOX_AGENT_TRIGGER`事件
  - [ ] 解析消息Frontmatter和内容
  - [ ] 根据消息类型和内容决定Agent调度策略
- [ ] 配置Prime Agent角色
  - [ ] 在`agent/defaults.py`中定义Prime Agent模板
  - [ ] 配置触发条件为`mailbox.agent.trigger`

### 3. 集成与扩展
- [ ] 在`CourierDaemon`中集成MailboxWatcher
  - [ ] 启动时自动初始化并启动watcher
  - [ ] 提供配置选项（轮询间隔、监听路径等）
- [ ] 扩展EventBus支持
  - [ ] 确保`MAILBOX_AGENT_TRIGGER`事件正确传播
  - [ ] 实现事件payload包含完整消息上下文
- [ ] 实现消息解析器
  - [ ] 重用`MailboxStore._parse_frontmatter()`
  - [ ] 提取关键信息：sender、content、mentions等

### 4. 智能路由与策略
- [ ] 实现基础路由策略
  - [ ] 命令模式：以`/`开头的消息触发特定Agent
  - [ ] @提及：`@Prime`触发Prime Agent
  - [ ] 关键词匹配：根据内容关键词路由
- [ ] 实现会话管理
  - [ ] 利用`session_id`关联相关消息
  - [ ] 维护会话上下文缓存

### 5. 测试与文档
- [ ] 单元测试
  - [ ] `MailboxWatcher`测试：文件创建检测、防抖逻辑
  - [ ] `MailboxAgentHandler`测试：事件处理、路由逻辑
  - [ ] 集成测试：端到端工作流验证
- [ ] 文档编写
  - [ ] API文档：新组件接口说明
  - [ ] 配置指南：如何启用和配置mailbox监听
  - [ ] 使用示例：典型场景配置示例

### 6. 性能优化与监控
- [ ] 性能优化
  - [ ] 优化文件系统监听性能
  - [ ] 实现批量消息处理
  - [ ] 添加资源使用监控
- [ ] 监控与日志
  - [ ] 添加详细的运行日志
  - [ ] 实现健康检查端点
  - [ ] 添加性能指标收集

## 技术设计要点

### 架构模式
1. **观察者模式**：MailboxWatcher作为观察者监听目录变化
2. **发布-订阅模式**：通过EventBus解耦组件
3. **策略模式**：可插拔的路由策略

### 关键决策
1. **轮询 vs 事件驱动**：采用轮询方式（PollingWatcher）保证跨平台兼容性
2. **防抖策略**：30秒窗口聚合流式消息，避免频繁触发
3. **错误处理**：分级错误处理，不影响主流程运行

### 依赖关系
- 依赖现有：`PollingWatcher`、`EventBus`、`AgentScheduler`、`MailboxStore`
- 新增组件：`MailboxWatcher`、`MailboxAgentHandler`、`PrimeAgentRole`

## 风险与缓解

### 技术风险
1. **性能问题**：频繁文件系统操作可能影响性能
   - **缓解**：合理设置轮询间隔，实现批量处理
2. **消息丢失**：处理过程中消息可能丢失
   - **缓解**：实现原子操作，添加重试机制
3. **Agent过载**：消息高峰导致Agent资源耗尽
   - **缓解**：实现限流和队列机制

### 业务风险
1. **误触发**：非预期消息触发Agent
   - **缓解**：实现精确的触发条件判断
2. **安全风险**：恶意消息触发危险操作
   - **缓解**：实现消息过滤和权限控制

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->