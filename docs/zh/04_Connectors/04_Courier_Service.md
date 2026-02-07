# Courier Service 设计

**Version**: 2.0.0
**Status**: Draft
**Related**: FEAT-0191, FEAT-XXXX

---

## 1. 概述

Courier 是 Monoco 的**用户级别全局 Mail 聚合服务**。它以单一守护进程形式运行，负责接收外部连续消息流、防抖聚合成 Mail、写入全局 inbox。

### 1.1 核心职责

| 职责 | 说明 |
|------|------|
| **Webhook 接收** | 接收外部平台推送，聚合成 Mail 写入全局 inbox |
| **Mail 聚合** | 防抖合并连续消息流，生成原子消费单位 |
| **验证与存储** | Schema 校验、去重、写入 `~/.monoco/mailbox/` |
| **状态 API** | 为 Mailbox CLI 提供状态管理接口 |

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
┌─────────────────────────────────────────────────────────────────┐
│                    Courier Service (Single Instance)             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Adapter    │  │   Adapter    │  │   Adapter    │           │
│  │    (Lark)    │  │   (Email)    │  │   (Slack)    │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           ▼                                     │
│                  ┌──────────────┐                               │
│                  │   Ingestion  │                               │
│                  │   Pipeline   │                               │
│                  └──────┬───────┘                               │
│                         │                                       │
│         ┌───────────────┼───────────────┐                       │
│         ▼               ▼               ▼                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │   Validate   │ │   Enrich     │ │   Deduplicate│            │
│  └──────┬───────┘ └──────────────┘ └──────────────┘            │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                              │
│  │  Global      │────► ~/.monoco/mailbox/                      │
│  │  Inbox       │      └── {source}/inbound/{timestamp}.jsonl  │
│  └──────────────┘                                              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    HTTP API Service                      │    │
│  │  POST /api/v1/messages/{id}/claim                       │    │
│  │  POST /api/v1/messages/{id}/complete                    │    │
│  │  POST /api/v1/messages/{id}/fail                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 存储结构

```
~/.monoco/mailbox/
├── lark/                       # 按 source 分目录
│   ├── inbound/                # 新 Mail（外部输入）
│   │   └── 20240115-103022-a7f3e8d2.jsonl
│   ├── outbound/               # 出站 Mail（待推送）
│   └── archive/                # 已归档
├── email/
│   ├── inbound/
│   ├── outbound/
│   └── archive/
└── slack/
    ├── inbound/
    ├── outbound/
    └── archive/
```

**设计约束**:
- 按 `source/status` 二级目录
- 文件名包含时间戳，不嵌套日期目录
- 不创建 manifest、attestations 等文件

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
class SingleInstanceLock:
    """用户级单实例锁"""

    def acquire(self) -> bool:
        pid_file = Path.home() / ".monoco" / "courier" / "courier.pid"

        if pid_file.exists():
            pid = int(pid_file.read_text())
            if self._process_exists(pid):
                return False  # 已有实例在运行

        pid_file.write_text(str(os.getpid()))
        return True
```

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

Courier 提供 HTTP API 供 Mailbox CLI 调用。

### 5.1 API 概览

| 端点 | 方法 | 说明 | 调用方 |
|------|------|------|--------|
| `/api/v1/mail/{id}/claim` | POST | 认领 Mail，移动到 processing | `mailbox claim` |
| `/api/v1/messages/{id}/complete` | POST | 标记完成，移动到 archive | `mailbox done` |
| `/api/v1/messages/{id}/fail` | POST | 标记失败，可能重试或归档 | `mailbox fail` |
| `/health` | GET | 健康检查 | 监控 |

### 5.2 认领 Mail

```http
POST /api/v1/messages/{id}/claim
Content-Type: application/json

{
    "agent_id": "agent_001",
    "workspace_path": "/Users/me/Projects/alpha"
}
```

**Courier 行为**:
1. 在全局 inbox 中查找 Mail
2. 从 `inbound/` 移动到 `processing/`
3. 记录认领信息
4. 返回成功响应

---

## 6. 与 Workspace 的关系

```
┌─────────────────────────────────────────────────────────────────┐
│                     Courier Service                              │
│                     (用户级单实例)                                │
│                                                                  │
│  职责:                                                           │
│  - 接收外部消息流，聚合成 Mail                                     │
│  - 写入 ~/.monoco/mailbox/                                 │
│  - 提供状态管理 API                                              │
│                                                                  │
│  不感知 workspace，不做路由                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 文件系统操作
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Workspace 层                                │
│                    (分散在各处目录)                               │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  ~/Proj/A    │  │ ~/Work/B     │  │ /Vol/ext/C   │           │
│  │              │  │              │  │              │           │
│  │ .monoco/     │  │ .monoco/     │  │ .monoco/     │           │
│  │  mailbox/    │  │  mailbox/    │  │  mailbox/    │           │
│  │   - 本地规则  │  │   - 本地规则  │  │   - 本地规则  │           │
│  │   - cursor   │  │   - cursor   │  │   - cursor   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
│  各 workspace:                                                   │
│  - 独立维护自己的 cursor                                          │
│  - 独立定义筛选规则                                               │
│  - 自主 CRUD 全局 inbox                                          │
└─────────────────────────────────────────────────────────────────┘
```

**关键设计**:
- Courier **不知道**有多少 workspace
- Workspace **不知道**其他 workspace 存在
- 通过**文件系统**作为唯一协调点

---

## 7. 配置设计

```yaml
# ~/.monoco/courier/config.yaml
courier:
  # 服务配置
  service:
    pid_file: "~/.monoco/courier/courier.pid"
    log_file: "~/.monoco/courier/courier.log"
    api_port: 8080              # 单一端口

  # 存储配置
  storage:
    inbox_path: "~/.monoco/mailbox"
    max_file_size: 10MB

  # 适配器配置
  adapters:
    lark:
      enabled: true
      webhook_path: "/webhook/lark"
      app_id: "${LARK_APP_ID}"
      app_secret: "${LARK_APP_SECRET}"

    email:
      enabled: true
      imap_server: "imap.gmail.com"
      imap_port: 993
      username: "${EMAIL_USERNAME}"
      password: "${EMAIL_PASSWORD}"
```

---

## 8. 监控与指标

### 8.1 关键指标

| 指标 | 类型 | 说明 |
|------|------|------|
| `courier_mail_received_total` | Counter | 接收 Mail 总数 |
| `courier_mail_by_provider` | Counter | 按 provider 分 Mail 数 |
| `courier_adapter_health` | Gauge | 适配器健康状态 |
| `courier_api_requests_total` | Counter | API 请求总数 |

### 8.2 健康检查

```bash
GET /health

{
    "status": "healthy",
    "instance": "user-level",
    "adapters": {
        "lark": {"status": "connected"},
        "email": {"status": "connected"}
    },
    "inbox_stats": {
        "new": 15,
        "processing": 3,
        "archive": 1024
    }
}
```

---

## 相关文档

- [01_Architecture](01_Architecture.md) - 整体架构设计
- [02_Mailbox_Protocol](02_Mailbox_Protocol.md) - Mail 协议 Schema 规范
- [03_Mailbox_CLI](03_Mailbox_CLI.md) - Mailbox CLI 命令设计
- [05_Courier_CLI](05_Courier_CLI.md) - Courier CLI 命令设计
