# Courier Service 设计

**Version**: 1.0.0
**Status**: Draft
**Related**: FEAT-0191

---

## 1. 概述

Courier 是 Monoco 的消息传输层，负责与外部通信平台（飞书、邮件、Slack等）进行双向消息收发。它以**守护进程（Daemon）**形式运行，管理连接、处理消息、维护状态。

### 1.1 核心职责

| 职责 | 说明 |
|------|------|
| **Webhook 接收** | 接收外部平台推送消息，处理后写入 `inbound/` |
| **消息发送** | 从 `outbound/` 读取草稿并实际发送 |
| **状态管理** | 维护消息锁状态（claim/done/fail），处理归档和重试 |
| **API 服务** | 为 Mailbox CLI 提供 HTTP API |

### 1.2 设计原则

1. **服务自治**: Courier 作为独立进程运行，不依赖 Agent 会话
2. **可靠投递**: 确保消息至少一次送达，失败自动重试
3. **防抖合并**: 快速连续消息合并处理，减少 Agent 触发频率
4. **优雅降级**: 单个适配器故障不影响其他适配器
5. **状态集中**: 消息状态由 Courier 统一管理，Agent 通过 API 交互

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Courier Service                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Adapter    │  │   Adapter    │  │   Adapter    │          │
│  │    (Lark)    │  │   (Email)    │  │   (Slack)    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           ▼                                    │
│                  ┌──────────────┐                              │
│                  │   Ingestion  │                              │
│                  │   Pipeline   │                              │
│                  └──────┬───────┘                              │
│                         │                                      │
│         ┌───────────────┼───────────────┐                      │
│         ▼               ▼               ▼                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │   Debounce   │ │   Validate   │ │   Enrich     │           │
│  │   Handler    │ │   Schema     │ │   Context    │           │
│  └──────┬───────┘ └──────────────┘ └──────────────┘           │
│         │                                                      │
│         ▼                                                      │
│  ┌──────────────┐                                             │
│  │   Mailbox    │                                             │
│  │    Store     │────► .monoco/mailbox/inbound/               │
│  └──────────────┘                                             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    Outbound Pipeline                     │  │
│  │  Draft ──► Validate ──► Queue ──► Send ──► Archive      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │  Lark   │          │  Email  │          │  Slack  │
   │ Server  │          │ Server  │          │ Server  │
   └─────────┘          └─────────┘          └─────────┘
```

### 2.2 组件职责

| 组件 | 职责 | 位置 |
|------|------|------|
| Adapter | 与外部平台通信，处理平台特定协议 | `courier/adapters/` |
| Ingestion Pipeline | 接收、验证、丰富入站消息 | `courier/pipeline/` |
| Debounce Handler | 防抖合并，减少重复触发 | `courier/debounce.py` |
| Mailbox Store | 将消息写入受保护的 Mailbox | `courier/store.py` |
| Outbound Pipeline | 处理出站消息发送 | `courier/outbound/` |
| Service Manager | 进程生命周期管理 | `courier/service.py` |

---

## 3. 服务生命周期

### 3.1 状态机

```
                    start
                      │
                      ▼
    ┌────────────────────────────────┐
    │                                │
    │  ┌──────────┐   kill/force   ┌─┴──────────┐
    │  │ stopped  │◄───────────────┤  running   │
    │  └────┬─────┘                └─┬──────────┘
    │       │                        │
    │       │ start                  │ stop
    │       ▼                        ▼
    │  ┌──────────┐                ┌──────────┐
    │  │ starting │───────────────►│ stopping │
    │  │ (init)   │    timeout     │ (cleanup)│
    │  └──────────┘                └────┬─────┘
    │                                   │
    │              restart              │
    └───────────────────────────────────┘
```

### 3.2 状态说明

| 状态 | 说明 |
|------|------|
| `stopped` | 服务未运行 |
| `starting` | 正在初始化适配器、建立连接 |
| `running` | 正常运行，收发消息 |
| `stopping` | 正在优雅关闭，完成进行中的任务 |
| `error` | 发生错误，可能正在重试 |

---

## 4. 适配器设计

### 4.1 适配器接口

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from dataclasses import dataclass

@dataclass
class AdapterConfig:
    """适配器配置基类"""
    provider: str
    enabled: bool = True
    retry_policy: dict = None

class BaseAdapter(ABC):
    """适配器基类"""

    @property
    @abstractmethod
    def provider(self) -> str:
        """返回 provider 标识"""
        pass

    @abstractmethod
    async def connect(self) -> None:
        """建立与外部平台的连接"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    async def listen(self) -> AsyncIterator[RawMessage]:
        """监听入站消息"""
        pass

    @abstractmethod
    async def send(self, message: OutboundMessage) -> SendResult:
        """发送出站消息"""
        pass

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """健康检查"""
        pass
```

### 4.2 适配器注册

```python
# courier/adapters/__init__.py
from typing import Dict, Type
from .base import BaseAdapter

_registry: Dict[str, Type[BaseAdapter]] = {}

def register_adapter(name: str, adapter_class: Type[BaseAdapter]):
    """注册适配器"""
    _registry[name] = adapter_class

def get_adapter(name: str) -> Type[BaseAdapter]:
    """获取适配器类"""
    return _registry.get(name)

def list_adapters() -> list[str]:
    """列出所有可用适配器"""
    return list(_registry.keys())

# 自动导入并注册
from .lark import LarkAdapter
from .email import EmailAdapter
from .slack import SlackAdapter

register_adapter("lark", LarkAdapter)
register_adapter("email", EmailAdapter)
register_adapter("slack", SlackAdapter)
```

---

## 5. 防抖合并（Debounce）

### 5.1 防抖策略

```python
@dataclass
class DebounceConfig:
    """防抖配置"""
    window_ms: int = 5000        # 防抖窗口（毫秒）
    max_wait_ms: int = 30000     # 最大等待时间
    key_extractor: Callable      # 消息分组键提取函数

class DebounceHandler:
    """
    防抖处理器

    将同一 session 的连续消息合并，减少 Agent 触发次数。
    """

    def __init__(self, config: DebounceConfig):
        self.config = config
        self._buffers: Dict[str, List[Message]] = {}
        self._timers: Dict[str, asyncio.Timer] = {}

    async def add(self, message: Message) -> Optional[List[Message]]:
        """
        添加消息到防抖缓冲区

        返回：如果触发刷新，返回消息列表；否则返回 None
        """
        key = self.config.key_extractor(message)

        if key not in self._buffers:
            self._buffers[key] = []
            # 启动定时器
            self._timers[key] = asyncio.create_task(
                self._flush_after(key, self.config.window_ms)
            )

        self._buffers[key].append(message)

        # 检查是否达到最大等待时间
        if self._should_flush(key):
            return await self._flush(key)

        return None

    async def _flush(self, key: str) -> List[Message]:
        """刷新缓冲区"""
        messages = self._buffers.pop(key, [])
        timer = self._timers.pop(key, None)
        if timer:
            timer.cancel()
        return messages
```

### 5.2 分组策略

```python
def session_thread_key_extractor(message: Message) -> str:
    """
    按 session + thread 分组

    同一聊天/话题的消息会被合并处理
    """
    session_id = message.session.id
    thread_key = message.session.thread_key or "_"
    return f"{session_id}:{thread_key}"
```

---

## 6. 入站流程

```
External Message
       │
       ▼
┌──────────────┐
│   Adapter    │──► 转换为内部 RawMessage
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Validate   │──► Schema 校验
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Enrich     │──► 补充上下文、下载附件
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Debounce   │──► 合并同一 session 的连续消息
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Write     │──► 写入 .monoco/mailbox/inbound/
└──────────────┘
       │
       ▼
  (Agent 读取 via Mailbox CLI)
```

---

## 7. HTTP API

Courier 提供 HTTP API 供 Mailbox CLI 调用，实现消息状态管理。

### 7.1 API 概览

| 端点 | 方法 | 说明 | 调用方 |
|------|------|------|--------|
| `/api/v1/messages/{id}/claim` | POST | 认领消息 | `mailbox claim` |
| `/api/v1/messages/{id}/complete` | POST | 标记完成 | `mailbox done` |
| `/api/v1/messages/{id}/fail` | POST | 标记失败 | `mailbox fail` |
| `/api/v1/messages/{id}` | GET | 获取消息状态 | 内部使用 |
| `/health` | GET | 健康检查 | 监控 |

### 7.2 认领消息

```http
POST /api/v1/messages/{id}/claim
Content-Type: application/json

{
    "agent_id": "agent_001",
    "timeout": 300
}
```

**响应**:
```json
{
    "success": true,
    "message_id": "lark_om_abc123",
    "status": "claimed",
    "claimed_by": "agent_001",
    "claimed_at": "2026-02-06T20:45:00Z",
    "expires_at": "2026-02-06T20:50:00Z"
}
```

**错误响应**:
```json
{
    "success": false,
    "error": "already_claimed",
    "claimed_by": "agent_002",
    "claimed_at": "2026-02-06T20:40:00Z"
}
```

### 7.3 标记完成

```http
POST /api/v1/messages/{id}/complete
Content-Type: application/json

{
    "agent_id": "agent_001"
}
```

**Courier 行为**:
1. 验证消息是否由 `agent_001` 认领
2. 更新状态为 `completed`
3. 移动到 `.monoco/mailbox/archive/`
4. 清理锁状态

### 7.4 标记失败

```http
POST /api/v1/messages/{id}/fail
Content-Type: application/json

{
    "agent_id": "agent_001",
    "reason": "API 超时",
    "retryable": true
}
```

**Courier 行为**:
1. 验证消息是否由 `agent_001` 认领
2. 更新状态为 `failed`，记录失败原因
3. 根据 `retryable` 和重试次数决定：
   - `retryable=true` 且未超次数：重新放入队列
   - 否则：移入 `.monoco/mailbox/.deadletter/`
4. 释放锁

### 7.5 锁状态存储

Courier 在内存中维护锁状态表，定期持久化到文件：

```
.monoco/mailbox/
└── .state/
    └── locks.json
```

```json
{
    "lark_om_abc123": {
        "status": "claimed",
        "claimed_by": "agent_001",
        "claimed_at": "2026-02-06T20:45:00Z",
        "expires_at": "2026-02-06T20:50:00Z"
    }
}
```

**锁超时机制**:
- 默认认领超时：5 分钟
- 超时后其他 Agent 可以强制认领（steal）
- 原认领者会收到 `claim_expired` 错误

---

## 8. 出站流程

```
Agent 执行 mailbox send
       │
       ▼
┌──────────────┐
│ Create Draft │──► 创建到 .monoco/mailbox/outbound/{provider}/
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Notify      │──► 通知 Courier（可选）
│  Courier     │
└──────┬───────┘
       │
       ▼
Courier 检测到新草稿 / 收到通知
       │
       ▼
┌──────────────┐
│   Validate   │──► 校验 Schema、权限
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Send      │──► 调用 Adapter 发送
└──────┬───────┘
       │
       ▼
   Success?
   ┌────┴────┐
   ▼         ▼
┌──────┐  ┌──────┐
│Move  │  │Retry │
│Archive 30d│  │Queue │
└──────┘  └──────┘
```

---

## 9. 错误处理与重试

### 8.1 重试策略

```python
@dataclass
class RetryPolicy:
    max_attempts: int = 3
    backoff_base_ms: int = 1000
    backoff_multiplier: float = 2.0
    max_backoff_ms: int = 30000

class RetryHandler:
    async def execute_with_retry(
        self,
        operation: Callable,
        policy: RetryPolicy
    ) -> Result:
        for attempt in range(policy.max_attempts):
            try:
                return await operation()
            except TransientError as e:
                if attempt == policy.max_attempts - 1:
                    raise
                wait_time = min(
                    policy.backoff_base_ms * (policy.backoff_multiplier ** attempt),
                    policy.max_backoff_ms
                )
                await asyncio.sleep(wait_time / 1000)
```

### 8.2 死信队列

发送失败且超过重试次数的消息进入死信队列：

```
.monoco/mailbox/
└── .deadletter/
    ├── lark/
    │   └── 20260206T204500_lark_abc123.md
    └── email/
        └── 20260206T204500_email_def456.md
```

---

## 9. 配置设计

```yaml
# .monoco/config/courier.yaml
courier:
  # 服务配置
  service:
    pid_file: ".monoco/run/courier.pid"
    log_file: ".monoco/log/courier.log"
    log_level: "info"

  # 防抖配置
  debounce:
    window_ms: 5000
    max_wait_ms: 30000

  # 适配器配置
  adapters:
    lark:
      enabled: true
      app_id: "${LARK_APP_ID}"
      app_secret: "${LARK_APP_SECRET}"
      encrypt_key: "${LARK_ENCRYPT_KEY}"
      webhook_port: 8080

    email:
      enabled: true
      imap_server: "imap.gmail.com"
      imap_port: 993
      smtp_server: "smtp.gmail.com"
      smtp_port: 587
      username: "${EMAIL_USERNAME}"
      password: "${EMAIL_PASSWORD}"
      poll_interval: 60

    slack:
      enabled: false
      bot_token: "${SLACK_BOT_TOKEN}"
```

---

## 10. 监控与指标

### 10.1 关键指标

| 指标 | 类型 | 说明 |
|------|------|------|
| `courier_messages_received_total` | Counter | 接收消息总数 |
| `courier_messages_sent_total` | Counter | 发送消息总数 |
| `courier_messages_failed_total` | Counter | 失败消息总数 |
| `courier_adapter_health` | Gauge | 适配器健康状态 |
| `courier_debounce_merged_total` | Counter | 合并的消息数 |
| `courier_processing_duration` | Histogram | 消息处理耗时 |

### 10.2 健康检查端点

```python
# 简单 HTTP 健康检查
GET /health

Response:
{
    "status": "healthy",  # healthy | degraded | unhealthy
    "adapters": {
        "lark": {"status": "connected", "last_ping": "2026-02-06T20:45:00Z"},
        "email": {"status": "connected", "last_poll": "2026-02-06T20:44:30Z"},
        "slack": {"status": "disabled"}
    },
    "uptime_seconds": 3600
}
```

---

## 相关文档

- [01_Architecture](01_Architecture.md) - 整体架构设计
- [02_Mailbox_Protocol](02_Mailbox_Protocol.md) - 消息协议 Schema 规范
- [03_Mailbox_CLI](03_Mailbox_CLI.md) - Mailbox CLI 命令设计
- [05_Courier_CLI](05_Courier_CLI.md) - Courier CLI 命令设计
