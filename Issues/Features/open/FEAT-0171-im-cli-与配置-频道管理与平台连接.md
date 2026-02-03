---
id: FEAT-0171
uid: 8e9b3d
type: feature
status: open
stage: draft
title: IM CLI 与配置：频道管理与平台连接
created_at: '2026-02-03T23:23:36'
updated_at: '2026-02-03T23:23:36'
parent: EPIC-0033
dependencies:
- FEAT-0167
domains:
- DevEx
tags:
- '#EPIC-0033'
- '#FEAT-0167'
- '#FEAT-0171'
files: []
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T23:23:36'
---

## FEAT-0171: IM CLI 与配置：频道管理与平台连接

## Objective
提供 CLI 工具和配置管理，支持 IM 频道管理、平台连接配置和状态监控。

### CLI 功能范围
- **平台连接**: 配置飞书、钉钉等平台的凭证
- **频道管理**: 查看、绑定、配置频道
- **状态监控**: 查看连接状态、消息统计
- **调试工具**: 测试消息发送、查看日志

## Acceptance Criteria
- [ ] 实现 `monoco im connect <platform>` 命令
- [ ] 实现 `monoco im channels` 命令
- [ ] 实现 `monoco im status` 命令
- [ ] 实现 `monoco im test` 调试命令
- [ ] 支持凭证加密存储
- [ ] 支持 project.yaml 配置热加载

## Technical Tasks
- [ ] 创建 `monoco/features/im/cli.py`
  - [ ] `monoco im connect feishu` - 交互式配置飞书
  - [ ] `monoco im connect dingtalk` - 交互式配置钉钉
  - [ ] `monoco im channels` - 列出已连接频道
  - [ ] `monoco im channels bind <channel_id> --project <id>` - 绑定项目
  - [ ] `monoco im status` - 显示连接状态和统计
  - [ ] `monoco im test send <channel_id> --message "..."` - 测试发送
  - [ ] `monoco im logs [--tail N]` - 查看消息日志
- [ ] 创建 `monoco/features/im/config.py`
  - [ ] IM 配置模型
  - [ ] 凭证加密/解密
  - [ ] 配置验证
- [ ] 更新 `project.yaml` 配置支持
  - [ ] `im.feishu.*` 配置项
  - [ ] `im.dingtalk.*` 配置项
  - [ ] `im.defaults.*` 默认配置
- [ ] 实现配置热加载
  - [ ] 监听 project.yaml 变化
  - [ ] 动态更新平台连接
- [ ] 创建配置向导
  - [ ] 飞书应用配置步骤
  - [ ] 钉钉应用配置步骤
  - [ ] Webhook URL 生成

## CLI 命令设计

```bash
# 平台连接
monoco im connect feishu --app-id cli_xxx --app-secret xxx
monoco im connect dingtalk --app-key ding_xxx --app-secret xxx

# 频道管理
monoco im channels list
monoco im channels show <channel_id>
monoco im channels bind <channel_id> --project my-project
monoco im channels config <channel_id> --auto-reply=true --default-agent=architect

# 状态与监控
monoco im status
monoco im stats --platform feishu

# 调试
monoco im test send <channel_id> --message "Hello"
monoco im test receive --payload '{...}'  # 模拟接收
```

## Configuration Schema

```yaml
# project.yaml
im:
  defaults:
    auto_reply: true
    require_mention: true
    context_window: 10
    
  feishu:
    enabled: true
    app_id: "cli_xxxxxxxx"
    app_secret: "encrypted:..."
    encrypt_key: "encrypted:..."
    event_types:
      - "im.message.receive_v1"
      
  dingtalk:
    enabled: true
    app_key: "ding_xxxxxxxx"
    app_secret: "encrypted:..."
    mode: "stream"
    
  channels:
    - channel_id: "oc_xxxxxxxx"
      name: "开发团队"
      platform: "feishu"
      project_binding: "my-project"
      auto_reply: true
      default_agent: "architect"
```

## Review Comments
