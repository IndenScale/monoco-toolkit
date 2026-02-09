# 钉钉 Stream 模式快速上手指南

> **无需公网 IP**，在内网/本地环境接收钉钉消息

## 5 分钟快速开始

### 1. 钉钉端配置（3分钟）

1. 登录 [钉钉开放平台](https://open.dingtalk.com/)
2. 创建「企业内部应用」→ 启用「机器人」
3. **关键步骤**：消息接收方式选择 **Stream 模式**
4. 记录 `AppKey` 和 `AppSecret`

### 2. 本地测试（2分钟）

```bash
# 安装依赖（首次）
pip install aiohttp

# 设置凭证
export DINGTALK_APP_KEY="your-app-key"
export DINGTALK_APP_SECRET="your-app-secret"

# 运行测试
python scripts/dingtalk_stream_demo.py
```

或使用 CLI：

```bash
monoco courier stream-test --app-key xxx --app-secret yyy
```

### 3. 验证连接

启动后，在钉钉中：
- 将机器人添加到一个群聊
- 或者直接在私聊中发送消息

你将在终端看到收到的消息：
```
📩 收到新消息
   项目: demo
   发送者: 张三
   内容: 你好，机器人！
```

## 集成到 Monoco

### 配置方式

**环境变量**（推荐开发环境）：
```bash
export DINGTALK_STREAM_APP_KEY="your-app-key"
export DINGTALK_STREAM_APP_SECRET="your-app-secret"
export DINGTALK_STREAM_DEFAULT_PROJECT="default"
```

**配置文件**（`.monoco/courier.yaml`）：
```yaml
dingtalk_stream:
  enabled: true
  app_key: "your-app-key"
  app_secret: "your-app-secret"
  default_project: "default"
  project_mapping:
    "cidxxxxxxxx": "project-alpha"
```

### 启动服务

```bash
# 启动 Courier（包含 Stream 适配器）
monoco courier start

# 查看状态
monoco courier status

# 查看日志
monoco courier logs -f
```

## 常见问题

**Q: Stream 模式和 Webhook 模式可以同时使用吗？**
A: 可以。Stream 用于接收，Webhook 用于发送，两者互补。

**Q: 为什么收不到消息？**
A: 检查清单：
- [ ] 机器人已添加到群聊（或被私聊）
- [ ] 机器人权限包含 `im.message.group`
- [ ] 应用已发布（即使是开发环境）
- [ ] 选择的是 Stream 模式而非 Webhook

**Q: 一个 Stream 连接可以服务多个项目吗？**
A: 可以，通过 `project_mapping` 按会话 ID 路由。

## 架构图

```
┌─────────────────┐         WebSocket          ┌──────────────────┐
│   Monoco CLI    │  ═══════════════════════►  │  钉钉 Stream 服务  │
│  (内网环境)      │   ◄────────────────────   │  (公网)           │
│                 │        推送消息            │                  │
│  Stream Adapter │                            │  用户发送消息      │
│  (无需公网IP)    │                            │        │         │
└────────┬────────┘                            └────────┼─────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐                            ┌──────────────────┐
│  Mailbox Store  │                            │   钉钉客户端      │
│  (本地文件系统)  │                            │  (手机/电脑)      │
└─────────────────┘                            └──────────────────┘
```

## 下一步

- 阅读完整文档：[dingtalk-stream-setup.md](./dingtalk-stream-setup.md)
- 了解多项目路由配置
- 查看 API 文档实现自定义消息处理
