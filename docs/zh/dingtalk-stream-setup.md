# 钉钉 Stream 模式配置指南

钉钉 Stream 模式（长连接模式）允许你在 **没有公网 IP** 的情况下接收钉钉消息。

## 原理对比

```
Webhook 模式（需要公网 IP）:
钉钉服务器 → HTTP POST → 你的服务器（公网可访问）

Stream 模式（无需公网 IP）:
钉钉服务器 ← WebSocket ← 你的客户端（主动连接，仅需可访问外网）
```

## 前置要求

1. **钉钉开放平台账号**（企业管理员或有权限的开发者）
2. **Python 依赖**（已包含在项目依赖中）
3. **外网访问能力**（能访问钉钉服务器，不需要公网 IP）

## 配置步骤

### 第一步：创建钉钉应用

1. 登录 [钉钉开放平台](https://open.dingtalk.com/)
2. 进入「应用开发」→「企业内部应用」→「创建应用」
3. 填写应用信息：
   - **应用名称**：Monoco IM
   - **应用类型**：H5微应用
   - **开发方式**：企业自主开发

### 第二步：启用机器人

1. 进入应用详情页 → 「机器人」→ 「启用」
2. 配置机器人：
   - **机器人名称**：Monoco Assistant
   - **消息接收方式**：选择 **Stream 模式** ⚠️ 重要！

3. 记录以下信息：
   - **AppKey**（Client ID）
   - **AppSecret**（Client Secret）

### 第三步：配置权限

在「权限管理」中开通以下权限：

- `im.message.group` - 接收群消息
- `im.message.p2p` - 接收单聊消息
- `dingtalk.corp.datacenter` - 企业数据中心访问

### 第四步：配置 Monoco

#### 方式 A：环境变量配置

```bash
# 在 .env 文件中添加
export DINGTALK_STREAM_APP_KEY="your-app-key"
export DINGTALK_STREAM_APP_SECRET="your-app-secret"
export DINGTALK_STREAM_DEFAULT_PROJECT="default"
```

#### 方式 B：配置文件（推荐）

在 `.monoco/courier.yaml` 中配置：

```yaml
dingtalk_stream:
  enabled: true
  app_key: "your-app-key"
  app_secret: "your-app-secret"
  default_project: "default"
  
  # 多项目路由（可选）
  project_mapping:
    "conversation_id_1": "project-alpha"
    "conversation_id_2": "project-beta"
  
  # 重连配置
  reconnect_interval: 5
  max_reconnect_attempts: 10
```

### 第五步：启动服务

```bash
# 启动 Courier（自动识别 Stream 配置）
monoco courier start

# 或使用 daemon 模式
monoco courier start --daemon

# 查看日志确认连接成功
monoco courier logs
```

预期输出：
```
[INFO] DingTalk Stream adapter connected successfully
[INFO] WebSocket connected with ticket: xxx...
```

## 使用方法

### 基本使用

1. **将机器人添加到群聊**
   - 在钉钉群中 @ 机器人
   - 或添加机器人为群成员

2. **发送消息**
   - 在群中 @机器人 或直接私聊机器人
   - 消息将自动写入项目的 mailbox

3. **查看消息**
   ```bash
   # 查看最新消息
   monoco mailbox list
   
   # 查看详情
   monoco mailbox read <message-id>
   ```

### 多项目路由

如果你有多个项目，可以通过群聊 ID 路由到不同项目：

```python
# 在配置中指定映射
dingtalk_stream:
  project_mapping:
    # 从钉钉群设置中获取 Conversation ID
    "cidxxxxxxxxxxxxxxxxxxxx": "monoco-core"
    "cidyyyyyyyyyyyyyyyyyyyy": "project-alpha"
```

获取 Conversation ID 的方法：
1. 在钉钉群中发送消息
2. 查看收到的消息元数据：`metadata.conversation_id`
3. 将 ID 添加到配置

## 故障排查

### 连接失败

```
[ERROR] Failed to get token: invalid appKey
```

- 检查 AppKey 和 AppSecret 是否正确
- 确认应用已发布（开发环境也需要发布）

### WebSocket 断开

```
[WARN] WebSocket closed by server
[INFO] Reconnecting in 5s (attempt 1/10)...
```

- 这是正常现象，适配器会自动重连
- 如果持续失败，检查网络连接

### 收不到消息

1. **检查权限**：确保已开通 `im.message.group` 权限
2. **检查机器人在群聊中**：确认机器人已被添加到群聊
3. **检查 Stream 模式**：在机器人设置中确认是 Stream 模式而非 Webhook

### 查看调试日志

```bash
# 启用调试模式
monoco courier start --debug

# 或设置环境变量
export MONOCO_LOG_LEVEL=debug
monoco courier start
```

## 高级配置

### 自定义消息处理器

```python
from monoco.features.courier.adapters.dingtalk_stream import create_dingtalk_stream_adapter

adapter = create_dingtalk_stream_adapter(
    app_key="your-key",
    app_secret="your-secret",
)

def handle_message(message, project_slug):
    """自定义消息处理"""
    print(f"收到消息 from {project_slug}: {message.content.text}")
    # 这里可以添加自定义逻辑

adapter.set_message_handler(handle_message)

# 启动监听
async for msg in adapter.listen():
    print(f"Message: {msg}")
```

### 回复消息

```python
# 回复某条消息（需要机器人被 @）
success = await adapter.reply_to_message(
    original_message=inbound_msg,
    content="收到！正在处理...",
    msg_type="text"
)
```

## 与 Webhook 模式对比

| 特性 | Stream 模式 | Webhook 模式 |
|------|------------|-------------|
| 公网 IP | ❌ 不需要 | ✅ 需要 |
| 配置复杂度 | 中 | 低 |
| 实时性 | ✅ 实时推送 | ✅ 实时推送 |
| 稳定性 | 高（自动重连） | 依赖网络环境 |
| 适用场景 | 内网/开发环境 | 生产/云环境 |
| 发送消息 | ⚠️ 需要额外配置 | ✅ 直接支持 |

## 建议

- **开发/测试**：使用 Stream 模式，无需配置 ngrok
- **生产环境**：如果已有公网 IP，Webhook 模式更成熟
- **混合模式**：可以 Stream 接收 + Webhook 发送
