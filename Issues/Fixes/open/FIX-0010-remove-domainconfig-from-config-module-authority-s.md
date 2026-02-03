---
id: FIX-0010
uid: ba9d29
type: fix
status: open
stage: doing
title: Remove DomainConfig from config module - authority should be Issues/Domains
  files
created_at: '2026-02-03T20:28:09'
updated_at: '2026-02-03T20:31:40'
parent: EPIC-0028
dependencies: []
related: []
domains:
- Foundation
tags:
- '#EPIC-0028'
- '#FIX-0010'
- config
- domain
- authority
files:
- monoco/core/config.py
- monoco/features/issue/domain_service.py
- monoco/features/issue/domain_commands.py
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T20:28:09'
---

## FIX-0010: Remove DomainConfig from config module - authority should be Issues/Domains files

## Problem Statement

当前 `monoco/core/config.py` 模块错误地包含了 `DomainConfig` 类，导致系统存在两个 Domain 定义来源：

1. **文件系统权威来源**: `Issues/Domains/*.md` —— 实际存储 Domain 定义
2. **配置模块缓存来源**: `MonocoConfig.domains` —— 从 workspace.yaml 读取（现已删除）

这种设计违反了"单一权威来源"原则，导致：
- Domain 变更需要同步修改两个地方
- `domain_service.py` 从 config 读取 Domain 列表，而非直接读取文件
- 配置与实际情况可能不一致

## Root Cause

```python
# monoco/core/config.py
class DomainConfig(BaseModel):
    items: List[DomainItem] = ...
    strict: bool = ...

class MonocoConfig(BaseModel):
    domains: DomainConfig = Field(default_factory=DomainConfig)  # ❌ 错误
```

## Solution

将 Domain 管理从 Config 模块彻底迁移到 File-based 管理：

1. **删除** `DomainConfig` 和 `DomainItem` 类从 `config.py`
2. **删除** `MonocoConfig.domains` 字段
3. **重构** `domain_service.py` 直接从 `Issues/Domains/*.md` 读取
4. **保留** `DomainService` API 不变（is_defined, get_canonical 等）

## Acceptance Criteria

- [ ] `monoco/core/config.py` 中不再包含任何 Domain 相关定义
- [ ] `MonocoConfig` 类不再有 `domains` 字段
- [ ] `domain_service.py` 直接从文件系统读取 Domain 定义
- [ ] `monoco domain list` 命令正常工作，显示 `Issues/Domains/*.md` 内容
- [ ] `monoco domain check` 命令正常工作，验证逻辑基于文件
- [ ] 所有引用 `get_config().domains` 的代码被修复
- [ ] workspace.yaml 中不再支持 `domains:` 配置（已删除）

## Technical Tasks

### Phase 1: 移除 Config 中的 Domain 定义
- [ ] 从 `monoco/core/config.py` 删除 `DomainItem` 类
- [ ] 从 `monoco/core/config.py` 删除 `DomainConfig` 类
- [ ] 从 `MonocoConfig` 删除 `domains: DomainConfig` 字段
- [ ] 删除 `DomainConfig.merge()` 方法

### Phase 2: 重构 DomainService
- [ ] 重写 `monoco/features/issue/domain_service.py`
  - [ ] `DomainService.__init__()` 接收 `workspace_root` 而非 `DomainConfig`
  - [ ] `DomainService.reload()` 从 `Issues/Domains/*.md` 解析
  - [ ] 保持公共 API 不变（`is_defined`, `is_canonical`, `get_canonical`, `normalize`, `suggest_correction`）
  - [ ] 添加 `list_domains()` 方法返回所有 Domain
- [ ] 创建 Domain 文件解析器（解析 Markdown front matter）

### Phase 3: 修复调用方
- [ ] 修复 `monoco/features/issue/domain_commands.py`
  - [ ] `list_domains()` 命令使用新的 `DomainService`
  - [ ] `check_domain()` 命令使用新的 `DomainService`
- [ ] 检查其他使用 `get_config().domains` 的代码
  - [ ] `monoco/features/issue/commands.py`
  - [ ] 其他可能引用的地方

### Phase 4: 清理与测试
- [ ] 删除遗留的 `domains` 相关配置加载逻辑
- [ ] 编写单元测试
  - [ ] DomainService 从文件读取测试
  - [ ] Domain 验证逻辑测试
- [ ] 手动验证
  - [ ] `monoco domain list` 正确显示
  - [ ] `monoco issue create` 的 `--domain` 参数验证正常

## Design Decisions

### Domain 文件格式
Domain 定义存储在 `Issues/Domains/<Name>.md`，格式：
```markdown
---
name: Foundation
description: Core foundation and framework-level infrastructure
---

## 定义
...
```

### 缓存策略
- `DomainService` 在初始化时加载所有 Domain 文件
- 提供 `reload()` 方法供需要时刷新
- 不做自动文件监听（简化实现，后续可按需添加）

## Review Comments

