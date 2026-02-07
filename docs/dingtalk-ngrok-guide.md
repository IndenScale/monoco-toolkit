# 钉钉无公网 IP 解决方案

由于钉钉 Stream 模式的 WebSocket 服务地址限制，推荐使用以下方案：

## 方案 1: ngrok 内网穿透（推荐开发环境）

### 1. 安装 ngrok

```bash
# macOS
brew install ngrok

# 或下载安装
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo gpg --dearmor -o /etc/apt/keyrings/ngrok.gpg && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list
```

### 2. 注册并配置

1. 访问 https://ngrok.com 注册账号
2. 获取 authtoken
3. 配置本地 ngrok

```bash
ngrok config add-authtoken YOUR_TOKEN
```

### 3. 启动 Courier 服务

```bash
# 启动 Courier（默认 8080 端口）
monoco courier start
```

### 4. 启动 ngrok 隧道

```bash
# 将本地 8080 映射到公网
ngrok http 8080
```

输出示例：
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8080
```

### 5. 配置钉钉 Webhook

在钉钉机器人设置中，将 Webhook 地址设置为：

```
https://abc123.ngrok-free.app/api/v1/courier/webhook/dingtalk/monoco-core
```

### 6. 测试

在钉钉群中 @机器人发送消息，即可在本地 Courier 中收到。

---

## 方案 2: Cloudflare Tunnel（推荐长期使用）

免费且可以获得固定域名。

```bash
# 安装
brew install cloudflared

# 登录
cloudflared tunnel login

# 创建隧道
cloudflared tunnel create monoco-courier

# 配置并启动
cloudflared tunnel route dns monoco-courier courier.yourdomain.com
cloudflared tunnel run monoco-courier
```

---

## 方案 3: 钉钉 Stream 模式（待验证）

钉钉 Stream 模式理论上不需要公网 IP，但目前官方 WebSocket 地址访问受限。

**状态**: 🔴 需要进一步验证正确的接入地址

替代方案是使用钉钉官方 Python SDK：

```bash
pip install dingtalk-stream
```

---

## 推荐

| 场景 | 方案 | 难度 |
|------|------|------|
| 快速测试 | ngrok | ⭐ 最简单 |
| 长期使用 | Cloudflare Tunnel | ⭐⭐ 需要域名 |
| 生产环境 | 云服务器 | ⭐⭐⭐ 需要服务器 |

对于当前无公网 IP 的情况，**强烈推荐使用 ngrok**，5 分钟即可完成配置。
