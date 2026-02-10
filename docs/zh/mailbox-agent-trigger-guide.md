# Mailbox目录监听与Prime Agent触发指南

**版本**: 1.0 (FEAT-0199)
**最后更新**: 2026-02-10
**适用版本**: Monoco v0.1.0+

## 概述

本功能实现了Monoco系统的自动化消息处理工作流。当外部消息（如DingTalk、Email等）到达mailbox时，系统会自动检测新消息文件，解析内容，并智能触发相应的Agent进行处理。

### 核心价值

1. **自动化响应**：外部消息到达后自动触发Agent处理，无需人工干预
2. **实时处理**：通过目录监听实现毫秒级响应
3. **智能路由**：基于消息内容智能调度合适的Agent
4. **会话管理**：维护对话上下文，提供连贯的交互体验

## 架构设计

### 组件架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  外部消息源     │───▶│   Courier       │───▶│   Mailbox       │
│  (DingTalk等)   │    │   Adapter       │    │   Inbound目录   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Agent调度器    │◀───│MailboxAgentHandler│◀───│MailboxInboundWatcher│
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │
        ▼
┌─────────────────┐
│   Prime Agent   │
│   (或其他Agent)  │
└─────────────────┘
```

### 数据流

1. **消息接收**：外部消息通过Courier适配器写入`.monoco/mailbox/inbound/{provider}/`
2. **文件检测**：`MailboxInboundWatcher`检测新文件创建
3. **事件触发**：触发`MAILBOX_INBOUND_RECEIVED`事件
4. **消息处理**：`MailboxAgentHandler`解析消息并路由
5. **Agent调度**：根据路由结果调度相应的Agent
6. **结果反馈**：Agent处理结果可通过outbound目录回复

## 快速开始

### 1. 启用Mailbox监听

Mailbox监听功能默认集成在Courier Daemon中。启动Courier时自动启用：

```bash
# 启动Courier Daemon（自动启用mailbox监听）
monoco courier start

# 查看运行状态
monoco courier status
```

### 2. 配置监听参数

通过环境变量配置监听行为：

```bash
# 设置轮询间隔（秒，默认2.0）
export MAILBOX_POLL_INTERVAL=1.0

# 设置防抖窗口（秒，默认30）
export MAILBOX_DEBOUNCE_WINDOW=15

# 设置监听路径（默认~/.monoco/mailbox）
export MAILBOX_ROOT=/path/to/custom/mailbox
```

### 3. 测试消息处理

创建测试消息文件验证功能：

```bash
# 创建测试消息目录
mkdir -p ~/.monoco/mailbox/inbound/dingtalk

# 创建测试消息文件
cat > ~/.monoco/mailbox/inbound/dingtalk/test_message.md << 'EOF'
---
id: test_msg_001
provider: dingtalk
session:
  id: test_chat_123
  type: group
  name: Test Group
participants:
  sender:
    id: u_test_001
    name: Test User
timestamp: '2026-02-10T10:00:00'
type: text
---
@Prime 请帮我创建一个新功能issue
EOF
```

观察日志输出：

```bash
# 查看Courier日志
tail -f ~/.monoco/logs/courier.log
```

预期输出：
```
INFO: Mailbox inbound watcher started
INFO: Detected new message: test_msg_001
INFO: Message routed to Prime Agent
INFO: Agent scheduled: mailbox_test_msg_001
```

## 配置详解

### Agent角色配置

系统预定义了多个Agent角色，可在`src/monoco/features/agent/defaults.py`中查看和修改：

```python
# 预定义角色
PRIME_AGENT = RoleTemplate(
    name="Prime",
    description="Primary agent for handling incoming messages",
    trigger="mailbox.agent.trigger",
    goal="Process incoming messages and initiate workflows",
    system_prompt="You are the Prime Agent...",
    engine="gemini",
)

HELPER_AGENT = RoleTemplate(
    name="Helper",
    description="Agent for providing explanations and guidance",
    trigger="help.request",
    goal="Provide clear explanations and helpful guidance",
    system_prompt="You are the Helper Agent...",
    engine="gemini",
)

# 更多角色：Drafter, Debugger, Architect, TaskManager
```

### 路由规则配置

消息路由基于`MessageRouter`的规则系统。默认规则包括：

1. **命令路由**：以`/`开头的消息
   - `/help` → Helper Agent
   - `/issue` → Drafter Agent
   - `/task` → TaskManager Agent

2. **提及路由**：@提及特定Agent
   - `@Prime` → Prime Agent
   - `@Architect` → Architect Agent

3. **关键词路由**：内容包含特定关键词
   - `bug|error|crash|fix` → Debugger Agent
   - `how to|what is|why|help with` → Helper Agent

4. **回退路由**：无匹配时使用Prime Agent

### 自定义路由规则

在项目配置中添加自定义路由规则：

```yaml
# .monoco/config.yaml
mailbox:
  routing_rules:
    - name: "custom_feature_request"
      condition: "keyword"
      pattern: "feature|enhancement|improvement"
      agent_role: "drafter"
      priority: 75
      enabled: true
    
    - name: "custom_urgent"
      condition: "keyword"
      pattern: "urgent|asap|critical"
      agent_role: "prime"
      priority: 95
      enabled: true
```

## 消息格式规范

### Inbound消息格式

Mailbox消息使用Markdown + YAML Frontmatter格式：

```yaml
---
id: 'dingtalk_msg_001'           # 消息唯一标识
provider: 'dingtalk'             # 消息源：dingtalk, email, slack等
session:                         # 会话信息
  id: 'chat_888'                # 会话ID
  type: 'group'                 # 会话类型：group, direct, thread
  name: 'Monoco Dev Group'      # 会话名称
participants:                    # 参与者
  sender:                       # 发送者
    id: 'u_1'
    name: 'IndenScale'
    role: 'owner'
  recipients: []                # 接收者列表
  cc: []                        # 抄送列表（Email专用）
  mentions: ['@Prime']          # 提及列表
timestamp: '2026-02-10T10:00:00' # 消息时间戳
type: 'text'                    # 消息类型：text, markdown, image, file
artifacts:                      # 附件信息
  - 'sha256:xxxx'              # 附件内容哈希
---
消息正文内容...

可以包含多行文本，
支持Markdown格式。
```

### 支持的Provider

当前支持的Provider类型：
- `dingtalk`：钉钉消息
- `email`：电子邮件
- `slack`：Slack消息（需适配器）
- `wechat`：微信消息（需适配器）

## 高级功能

### 会话管理

系统自动维护会话上下文：

```python
# 会话数据结构
session = {
    "id": "chat_888",           # 会话ID
    "provider": "dingtalk",     # 消息源
    "created_at": datetime,     # 创建时间
    "last_activity": datetime,  # 最后活动时间
    "message_count": 5,         # 消息数量
    "agent_tasks": [            # 关联的Agent任务
        "agent_task_001",
        "agent_task_002"
    ],
    "context": {                # 会话上下文
        "last_topic": "bug报告",
        "priority": "high",
        "assigned_agent": "debugger"
    }
}
```

### 防抖机制

为避免频繁触发Agent，系统实现消息防抖：

1. **防抖窗口**：默认30秒，窗口内消息被聚合
2. **会话隔离**：不同会话独立防抖
3. **批量处理**：窗口结束后批量处理所有消息

配置防抖参数：
```bash
# 缩短防抖窗口（秒）
export MAILBOX_DEBOUNCE_WINDOW=10

# 禁用防抖（开发调试）
export MAILBOX_DEBOUNCE_WINDOW=0
```

### 性能监控

查看系统运行状态：

```bash
# 查看Mailbox组件状态
monoco courier stats

# 查看会话统计
monoco mailbox sessions

# 查看路由统计
monoco mailbox routing-stats
```

## 故障排除

### 常见问题

**Q1: 消息未被检测到**
```
检查步骤：
1. 确认Courier Daemon正在运行
2. 检查消息文件路径：~/.monoco/mailbox/inbound/{provider}/
3. 验证文件格式（必须有YAML Frontmatter）
4. 查看日志：tail -f ~/.monoco/logs/courier.log
```

**Q2: Agent未被触发**
```
检查步骤：
1. 确认消息包含有效的触发条件（命令、提及、关键词）
2. 检查路由规则配置
3. 验证Agent角色配置
4. 查看事件日志：grep "MAILBOX" ~/.monoco/logs/event.log
```

**Q3: 性能问题**
```
优化建议：
1. 增加轮询间隔：export MAILBOX_POLL_INTERVAL=5.0
2. 调整防抖窗口：export MAILBOX_DEBOUNCE_WINDOW=60
3. 限制并发Agent数量
4. 监控系统资源使用
```

### 日志分析

关键日志信息：

```log
# 正常流程
INFO: Mailbox inbound watcher started
INFO: Detected new file: /path/to/message.md
INFO: Extracted metadata: provider=dingtalk, session_id=chat_888
INFO: Event published: MAILBOX_INBOUND_RECEIVED
INFO: Message buffered for session: chat_888
INFO: Processing 3 buffered messages
INFO: Message routed to: Prime (rule: prime_mention)
INFO: Agent scheduled: mailbox_msg_001

# 错误情况
ERROR: Failed to parse message file: Invalid frontmatter
WARNING: No routing rule matched, using fallback
ERROR: Failed to schedule agent: Engine not available
```

## 扩展开发

### 添加新的Provider

1. 创建Provider适配器：
```python
# src/monoco/features/courier/adapters/new_provider.py
class NewProviderAdapter:
    def handle_webhook(self, payload):
        # 处理webhook，写入mailbox
        message = self._parse_payload(payload)
        store.create_inbound_message(message)
```

2. 注册Provider：
```python
# 在Courier配置中注册
PROVIDER_REGISTRY.register('new_provider', NewProviderAdapter)
```

3. 创建目录结构：
```bash
mkdir -p ~/.monoco/mailbox/inbound/new_provider
```

### 自定义路由策略

继承`MessageRouter`实现自定义路由：

```python
class CustomMessageRouter(MessageRouter):
    def __init__(self):
        super().__init__()
        # 添加自定义规则
        self.add_rule(RoutingRule(
            name="custom_analysis",
            condition="regex",
            pattern=r"analyze|report|statistics",
            agent_role="analyst",
            priority=80
        ))
    
    def route_message(self, context):
        # 自定义路由逻辑
        if self._is_urgent(context):
            return "prime", {"reason": "urgent"}
        return super().route_message(context)
```

## 最佳实践

### 生产环境部署

1. **资源规划**：
   - 确保足够的磁盘空间存储mailbox文件
   - 配置合理的轮询间隔（建议2-5秒）
   - 设置Agent并发限制

2. **监控告警**：
   - 监控mailbox目录大小
   - 设置Agent执行超时告警
   - 监控消息处理延迟

3. **备份策略**：
   - 定期备份mailbox/archive目录
   - 保留消息处理日志
   - 实现消息重放机制

### 开发调试

1. **调试模式**：
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
export MAILBOX_DEBUG=true

# 手动触发处理
monoco mailbox process <message_id>
```

2. **测试工具**：
```bash
# 发送测试消息
monoco mailbox test-message \
  --provider dingtalk \
  --content "@Prime 测试消息" \
  --sender "测试用户"

# 查看处理结果
monoco mailbox status <message_id>
```

## 版本历史

- **v1.0 (2026-02-10)**: FEAT-0199 初始版本
  - 实现Mailbox目录监听
  - 集成Prime Agent触发
  - 支持智能消息路由
  - 完整的测试覆盖

- **计划功能**:
  - 支持更多消息源（Email、Slack）
  - 增强路由策略（机器学习）
  - 可视化监控面板
  - 消息优先级队列

## 获取帮助

- 查看完整文档：`monoco docs mailbox`
- 报告问题：GitHub Issues
- 社区讨论：Monoco Discord
- 紧急支持：联系维护团队

---

**注意**: 本功能处于活跃开发阶段，API可能发生变化。建议在生产环境部署前进行充分测试。