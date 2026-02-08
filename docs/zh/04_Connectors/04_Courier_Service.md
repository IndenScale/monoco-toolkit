# Courier Service 设计

**Version**: 2.1.0
**Status**: Implemented
**Related**: FEAT-0191, FEAT-0172, FEAT-0189

---

## 1. 概述

Courier 是 Monoco 的**用户级别全局 Mail 聚合服务**。它以单一守护进程形式运行，负责接收外部连续消息流、防抖聚合成 Mail、写入全局 inbox。

### 1.1 核心职责

| 职责             | 说明                                            |
| ---------------- | ----------------------------------------------- |
| **Webhook 接收** | 接收外部平台推送（钉钉 Stream、Webhook）        |
| **Mail 聚合**    | 防抖合并连续消息流（5秒窗口），生成原子消费单位 |
| **验证与存储**   | Schema 校验、写入 `~/.monoco/mailbox/inbound/`  |
| **状态管理**     | 锁管理（claim）、归档（done）、死信（fail）     |
| **出站处理**     | 轮询 `outbound/` 并发送消息                     |
| **HTTP API**     | 提供状态管理接口（端口 8644）                   |

### 1.2 设计原则

1. **用户级单实例**: 一个用户设备只运行一个 Courier 进程
2. **Mail 聚合**: 连续消息流防抖聚合成原子消费单位
3. **只写不路由**: 写入全局 inbox，不决定 Mail 归属哪个 workspace
4. **无状态感知**: 不维护 workspace 列表，不感知其存在
5. **平铺存储**: 按 `status/source` 二级目录，时间戳在文件名

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Courier Service (Single Instance)                     │
│                                                                              │
│  Inbound Pipeline                                                            │
│  ─────────────                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Adapter    │───▶│   Debounce   │───▶│   Validate   │                   │
│  │  (DingTalk)  │    │   Handler    │    │   & Enrich   │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                   │                         │
│                                                   ▼                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     State Management                                 │   │
│  │  ┌─────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │   │
│  │  │ LockManager │  │ MessageStateManager │  │  DebounceConfig     │  │   │
│  │  │  (.state/)  │  │ (archive/deadletter)│  │  (5s window)        │  │   │
│  │  └─────────────┘  └─────────────────────┘  └─────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Storage (~/.monoco/mailbox/)                 │   │
│  │  ├── inbound/{provider}/    # 新消息 (write)                         │   │
│  │  ├── outbound/{provider}/   # 待发送 (read)                          │   │
│  │  ├── archive/{provider}/    # 已完成 (move)                          │   │
│  │  ├── .deadletter/{prov}/    # 死信 (move)                            │   │
│  │  └── .state/locks.json      # 锁状态                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Outbound Pipeline                                                           │
│  ──────────────                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Watcher    │───▶│   Outbound   │───▶│   Adapter    │                   │
│  │  (outbound/) │    │   Processor  │    │   (Send)     │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                                              │
│  HTTP API (:8644)                                                            │
│  ───────────────                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  POST /api/v1/messages/{id}/claim                                   │   │
│  │  POST /api/v1/messages/{id}/complete                                │   │
│  │  POST /api/v1/messages/{id}/fail                                    │   │
│  │  GET  /health                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 存储结构

```
~/.monoco/
├── mailbox/                    # Mail 存储根目录
│   ├── inbound/                # 入站消息（按 provider 分目录）
│   │   ├── lark/
│   │   ├── email/
│   │   ├── slack/
│   │   └── dingtalk/
│   ├── outbound/               # 出站消息（待发送）
│   │   ├── lark/
│   │   ├── email/
│   │   └── dingtalk/
│   ├── archive/                # 已归档消息
│   │   ├── lark/
│   │   ├── email/
│   │   └── dingtalk/
│   ├── .state/                 # 状态目录
│   │   └── locks.json          # 消息锁状态
│   └── .deadletter/            # 死信队列
│       ├── lark/
│       ├── email/
│       └── dingtalk/
│
├── run/                        # 运行时文件
│   ├── courier.pid             # 进程 ID
│   ├── courier.json            # 运行时状态（host, port, started_at）
│   └── courier.lock            # 单实例文件锁
│
└── log/
    └── courier.log             # 服务日志
```

**设计约束**:

- 按 `provider` 分目录，状态体现在 locks.json 而非目录
- 文件名格式: `{YYYYMMDDTHHMMSS}_{provider}_{uid}.md`
- Markdown + YAML Frontmatter 格式
- 状态集中存储在 `.state/locks.json`

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

### 3.2 单实例保证

```python
# Courier 启动时检查
class CourierService:
    """管理 Courier 守护进程生命周期"""

    PID_FILE = Path.home() / ".monoco" / "run" / "courier.pid"
    LOCK_FILE = Path.home() / ".monoco" / "run" / "courier.lock"

    def _acquire_lock(self) -> None:
        """获取文件锁防止多实例"""
        self._lock_fd = os.open(self.lock_file, os.O_CREAT | os.O_RDWR)
        fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _write_pid(self, pid: int) -> None:
        """原子写入 PID 文件（使用 O_EXCL）"""
        fd = os.open(self.pid_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(pid).encode())
        os.close(fd)
```

**启动流程**:

1. 尝试获取文件锁 (`courier.lock`)
2. 检查 PID 文件是否存在且进程存活
3. 原子创建 PID 文件（防止竞态）
4. 写入状态文件 (`courier.json`) 记录 host/port/started_at

---

## 4. 适配器设计

### 4.1 适配器接口

```python
from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    """适配器基类"""

    @property
    @abstractmethod
    def provider(self) -> str:
        """返回 provider 标识"""
        pass

    @abstractmethod
    async def start(self, courier: "Courier") -> None:
        """启动适配器，注册路由到 Courier"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """停止适配器"""
        pass

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """健康检查"""
        pass
```

### 4.2 Mail 写入

```python
class Courier:
    """用户级全局 Courier 服务"""

    async def receive_message(
        self,
        provider: str,
        raw_message: dict
    ) -> None:
        """
        接收外部消息流，聚合成 Mail，验证后写入全局 inbox
        """
        # 1. 验证格式
        validated = self.validate(raw_message)

        # 2. 补充元数据
        enriched = self.enrich(validated, provider)

        # 3. 生成文件名
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        msg_hash = hashlib.sha256(
            json.dumps(enriched, sort_keys=True).encode()
        ).hexdigest()[:8]
        filename = f"{timestamp}-{msg_hash}.jsonl"

        # 4. 写入全局 inbox
        inbox_path = (
            Path.home() /
            ".monoco/mailbox" /
            provider /
            "inbound" /
            filename
        )
        inbox_path.parent.mkdir(parents=True, exist_ok=True)
        inbox_path.write_text(json.dumps(enriched))

        # 5. 触发文件系统事件（供 workspace 监听）
        # 可选: 发送通知给已连接的 workspace
```

---

## 5. HTTP API

Courier 提供 HTTP API（默认端口 **8644**）供 Mailbox CLI 调用。

### 5.1 API 概览

| 端点                             | 方法 | 说明                     | 调用方          |
| -------------------------------- | ---- | ------------------------ | --------------- |
| `/api/v1/messages/{id}/claim`    | POST | 认领消息，创建锁         | `mailbox claim` |
| `/api/v1/messages/{id}/complete` | POST | 标记完成，归档           | `mailbox done`  |
| `/api/v1/messages/{id}/fail`     | POST | 标记失败，触发重试或死信 | `mailbox fail`  |
| `/health`                        | GET  | 健康检查                 | 监控            |

### 5.2 认领消息

```http
POST /api/v1/messages/{id}/claim
Content-Type: application/json

{
    "agent_id": "agent_001",
    "timeout": 300
}
```

**请求参数**:

- `agent_id`: 认领者标识
- `timeout`: 锁超时时间（秒，默认 300）

**Courier 行为**:

1. 检查消息是否存在于 `inbound/`
2. 检查是否已被其他 agent 认领
3. 在 `.state/locks.json` 中创建锁记录
4. 设置过期时间（默认 5 分钟）
5. 返回 `LockEntry`

### 5.3 完成消息

```http
POST /api/v1/messages/{id}/complete
Content-Type: application/json

{
    "agent_id": "agent_001"
}
```

**Courier 行为**:

1. 验证由当前 agent 认领
2. 更新 locks.json 状态为 `completed`
3. 将消息文件移动到 `archive/{provider}/`
4. 清理锁记录

### 5.4 失败消息

```http
POST /api/v1/messages/{id}/fail
Content-Type: application/json

{
    "agent_id": "agent_001",
    "reason": "API timeout",
    "retryable": true
}
```

**Courier 行为**:

1. 验证由当前 agent 认领
2. 如果 `retryable=true` 且重试次数 < 3:
   - 增加重试计数
   - 更新状态为 `new`（等待重新认领）
   - 应用指数退避延迟
3. 如果 `retryable=false` 或重试次数 >= 3:
   - 更新状态为 `deadletter`
   - 移动到 `.deadletter/{provider}/`

---

## 8. 核心组件详解

### 8.1 LockManager

管理消息认领锁，确保同一消息不会被多个 agent 同时处理。

```python
class LockManager:
    """线程安全的锁管理器"""

    def claim_message(self, message_id: str, agent_id: str, timeout: int = 300) -> LockEntry
    def complete_message(self, message_id: str, agent_id: str) -> None
    def fail_message(self, message_id: str, agent_id: str, reason: str, retryable: bool) -> LockEntry
    def get_status(self, message_id: str) -> MessageStatus
```

**特性**:

- 基于文件锁（`locks.json`）的持久化
- 自动清理过期锁（启动时检查）
- 线程安全（使用 `threading.RLock`）

### 8.2 DebounceHandler

防抖处理连续到达的消息，将同一 session 的短消息聚合。

```python
class DebounceHandler:
    """消息防抖处理器"""

    async def add(self, message: InboundMessage) -> Optional[List[InboundMessage]]
    async def flush_all(self) -> Dict[str, List[InboundMessage]]
```

**默认配置**:

- `window_ms`: 5000ms（5 秒窗口）
- `max_wait_ms`: 30000ms（最大等待 30 秒）
- 按 `session_id:thread_key` 分组

### 8.3 MessageStateManager

协调锁管理与文件系统操作：

```python
class MessageStateManager:
    def archive_message(self, message_id: str) -> Optional[Path]
    def move_to_deadletter(self, message_id: str) -> Optional[Path]
    def get_retry_delay_ms(self, retry_count: int) -> int
```

---

## 6. 配置与常量

### 6.1 默认配置

| 配置项                         | 默认值      | 说明                             |
| ------------------------------ | ----------- | -------------------------------- |
| `COURIER_DEFAULT_HOST`         | `localhost` | API 绑定地址                     |
| `COURIER_DEFAULT_PORT`         | `8644`      | API 端口（避免与常用 8080 冲突） |
| `CLAIM_TIMEOUT_SECONDS`        | `300`       | 认领超时（5 分钟）               |
| `MAX_RETRY_ATTEMPTS`           | `3`         | 最大重试次数                     |
| `RETRY_BACKOFF_BASE_MS`        | `1000`      | 退避基数（1 秒）                 |
| `RETRY_MAX_BACKOFF_MS`         | `30000`     | 最大退避（30 秒）                |
| `DEFAULT_DEBOUNCE_WINDOW_MS`   | `5000`      | 防抖窗口（5 秒）                 |
| `DEFAULT_DEBOUNCE_MAX_WAIT_MS` | `30000`     | 最大等待（30 秒）                |
| `ARCHIVE_RETENTION_DAYS`       | `30`        | 归档保留天数                     |
| `SERVICE_START_TIMEOUT`        | `30`        | 服务启动超时                     |
| `SERVICE_STOP_TIMEOUT`         | `30`        | 服务停止超时                     |

### 6.2 配置文件示例

```yaml
# ~/.monoco/courier/config.yaml
courier:
  # 服务配置
  service:
    host: 'localhost'
    port: 8644
    log_level: 'info'

  # 存储配置
  storage:
    mailbox_root: '~/.monoco/mailbox'

  # 防抖配置
  debounce:
    window_ms: 5000
    max_wait_ms: 30000

  # 适配器配置
  adapters:
    dingtalk:
      enabled: true
      app_key: '${DINGTALK_APP_KEY}'
      app_secret: '${DINGTALK_APP_SECRET}'
```

---

## 7. 监控与指标

### 7.1 健康检查

```bash
GET /health

{
    "status": "healthy",
    "version": "1.0.0",
    "adapters": {
        "dingtalk": {"status": "connected", "mode": "stream"}
    },
    "metrics": {
        "messages_received": 152,
        "messages_sent": 43,
        "messages_pending": 5,
    }
}
```

### 7.2 日志查看

```bash
# 查看日志
monoco courier logs

# 清理日志
monoco courier logs clean
```

---

## 相关文档

- [01_Architecture](01_Architecture.md) - 整体架构设计
- [02_Mailbox_Protocol](02_Mailbox_Protocol.md) - Mail 协议 Schema 规范
- [03_Mailbox_CLI](03_Mailbox_CLI.md) - Mailbox CLI 命令设计
- [05_Courier_CLI](05_Courier_CLI.md) - Courier CLI 命令设计
