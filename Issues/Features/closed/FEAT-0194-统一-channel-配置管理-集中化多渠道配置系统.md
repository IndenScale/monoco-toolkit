---
id: FEAT-0194
uid: 25ec29
type: feature
status: closed
stage: done
title: 统一 Channel 配置管理：集中化多渠道配置系统
created_at: '2026-02-07T19:30:49'
updated_at: '2026-02-07T19:51:25'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0194'
files:
- .gitignore
- src/monoco/features/channel/__init__.py
- src/monoco/features/channel/commands.py
- src/monoco/features/channel/courier_integration.py
- src/monoco/features/channel/migrate.py
- src/monoco/features/channel/models.py
- src/monoco/features/channel/sender.py
- src/monoco/features/channel/store.py
- src/monoco/features/courier/api.py
- src/monoco/main.py
criticality: medium
solution: implemented # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-07T19:30:49'
isolation:
  type: branch
  ref: FEAT-0194-统一-channel-配置管理-集中化多渠道配置系统
  created_at: '2026-02-07T19:36:55'
---

## FEAT-0194: 统一 Channel 配置管理：集中化多渠道配置系统

## Objective

当前 Monoco 的消息渠道配置分散在多个地方：
- `.env` 文件存储钉钉 Webhook URL 和关键词（临时方案）
- `~/.monoco/inventory.json` 存储项目映射和简单配置
- 缺少统一的多渠道管理模型

本 Feature 旨在建立统一的 **Channel 配置管理系统**，实现：
1. **集中存储**: 所有渠道配置统一存储在 `~/.monoco/channels.yaml`
2. **多租户支持**: 支持多个同类型渠道（如多个钉钉群）
3. **类型抽象**: 统一支持 dingtalk、lark、email 等多种渠道类型
4. **安全管理**: 敏感信息加密存储
5. **便捷管理**: 提供 `monoco channel` CLI 命令管理渠道

## Acceptance Criteria

- [x] 创建 `~/.monoco/channels.yaml` 配置文件格式标准
- [x] 实现 Channel 配置数据模型和验证
- [x] 支持 dingtalk webhook 渠道类型
- [x] 支持 lark webhook 渠道类型
- [x] 支持 email smtp 渠道类型
- [x] 实现 `monoco channel list` 命令查看所有渠道
- [x] 实现 `monoco channel add <type>` 命令添加渠道
- [x] 实现 `monoco channel remove <id>` 命令删除渠道
- [x] 实现 `monoco channel test <id>` 命令测试渠道连通性
- [x] 实现 `monoco channel send <id> <message>` 命令发送消息
- [x] Courier 适配器支持通过 Channel ID 发送消息
- [x] 迁移现有 `.env` 配置到新的 Channel 系统

## Technical Tasks

- [x] **设计 Channel 配置 Schema**
  - [x] 定义 `Channel` 基础数据模型 (models.py)
  - [x] 定义 `DingtalkChannel`、`LarkChannel`、`EmailChannel` 子类型
  - [x] 定义 `ChannelStore` 管理类接口

- [x] **实现配置存储层**
  - [x] 创建 `monoco/features/channel/store.py`
  - [x] 实现 `channels.yaml` 读写操作
  - [x] 实现配置验证
  - [x] 配置序列化/反序列化

- [x] **实现 CLI 命令**
  - [x] 创建 `monoco/features/channel/commands.py`
  - [x] 实现 `channel list` 命令
  - [x] 实现 `channel add` 命令（支持交互式配置）
  - [x] 实现 `channel remove` 命令
  - [x] 实现 `channel test` 命令
  - [x] 实现 `channel send` 命令
  - [x] 实现 `channel show` 命令
  - [x] 实现 `channel default` 命令
  - [x] 实现 `channel migrate` 命令

- [x] **集成 Courier 系统**
  - [x] 创建 `ChannelCourierAdapter` 桥接类
  - [x] 更新 Courier API 支持 Channel 端点
  - [x] `/api/v1/courier/channels/send` - 发送到默认渠道
  - [x] `/api/v1/courier/channels/{id}/send` - 发送到指定渠道
  - [x] `/api/v1/courier/channels` - 列出所有渠道
  - [x] `/api/v1/courier/channels/health` - 渠道健康检查

- [x] **迁移和兼容性**
  - [x] 编写配置迁移脚本 `migrate.py`
  - [x] 支持从 `.env` 自动迁移 DingTalk 配置
  - [x] 提供 `monoco channel migrate` 命令

## Channel 配置示例

```yaml
# ~/.monoco/channels.yaml
version: "1.0"

channels:
  dingtalk:
    - id: "dt-monoco-dev"
      name: "Monoco 开发群"
      type: "webhook"
      webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
      keywords: "monoco"
      secret: ""
      enabled: true
      created_at: "2026-02-07T12:00:00Z"
      
  lark:
    - id: "lk-monoco"
      name: "飞书测试群"
      type: "webhook"
      webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
      enabled: true
      
  email:
    - id: "email-alerts"
      name: "告警邮箱"
      type: "smtp"
      smtp_host: "smtp.gmail.com"
      smtp_port: 587
      username: "alerts@example.com"
      password: "encrypted:xxx"
      use_tls: true
      enabled: false

defaults:
  send: "dt-monoco-dev"
  receive: ["dt-monoco-dev"]
```

## CLI 使用示例

```bash
# 列出所有渠道
monoco channel list

# 添加钉钉渠道
monoco channel add dingtalk \
  --id dt-monoco-dev \
  --name "Monoco 开发群" \
  --webhook "https://oapi.dingtalk.com/robot/send?access_token=xxx" \
  --keywords "monoco"

# 测试渠道
monoco channel test dt-monoco-dev

# 发送消息
monoco channel send dt-monoco-dev "Hello, 钉钉！"

# 删除渠道
monoco channel remove dt-monoco-dev
```

## Related Issues

- FEAT-0190: 钉钉平台适配器
- FEAT-0193: 全局项目注册表

## Review Comments


## Review Comments

### Self-Review

- [x] 所有 Acceptance Criteria 已完成
- [x] CLI 命令已实现并测试：list, add, remove, test, send, show, default, migrate
- [x] Courier API 集成完成：新增 channels 相关端点
- [x] 代码遵循项目现有风格（Rich/Typer）
- [x] 配置文件格式清晰，易于手动编辑

### Notes

- 加密功能预留了接口但未完全实现，后续可通过环境变量或密钥管理系统增强
- Lark 和 Email 渠道的测试已实现基础功能，需要真实凭证验证
- 迁移脚本支持从 .env 读取 DingTalk 配置并自动转换
