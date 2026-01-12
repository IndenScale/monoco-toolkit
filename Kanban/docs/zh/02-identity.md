# 身份与权限 (Identity & Security)

Monoco Kanban 采用 **"物理层 + 策略层"** 的双层权限模型，旨在平衡去中心化的灵活性与企业级的管控需求。

## 1. 核心原则

> **Git Identity is the User Identity.**

我们不强制引入一套全新的账号体系。如果 Git 承认你的身份，Kanban 就承认你的身份。

## 2. 层级模型

### Layer 1: 物理层 (The Physics)

**机制**: `Repo URL + Git Config (Email/Name)`

这是 Kanban 本地版（Desktop）的基础运行模式。

- **认证 (Authentication)**:
  - 读取本地 `git config user.email` 确定当前操作者身份。
  - 依赖 SSH Key / HTTPS Token 与远程仓库通信。
- **鉴权 (Authorization)**:
  - **Read**: 如果你有仓库的 Clone 权限，你就能查看所有任务。
  - **Write**: 如果你有仓库的 Push 权限，你就能修改所有任务。
- **适用场景**: 个人开发者、开源项目、小型初创团队。

### Layer 2: 策略层 (The Policy)

**机制**: `SaaS Account + RBAC as Code`

当需要更细粒度的权限控制时（例如：实习生只能评论，不能移动卡片），通过 SaaS 层叠加策略。

- **身份绑定**: 用户在 Monoco SaaS 登录（GitHub/Google），并验证其 Git Email 所有权。
- **策略文件**: 权限规则存储在代码库中（例如 `.monoco/policy.yaml`），受 Git 版本控制。
  ```yaml
  roles:
    maintainer: ["alice@example.com"]
    guest: ["*@temp.com"]
  permissions:
    guest:
      - "issue:read"
      - "issue:comment"
      # 禁止 "issue:update_status"
  ```
- **执行**:
  - **UI 层**: Kanban 解析策略文件，根据当前用户身份禁用特定按钮。
  - **Server 层**: Monoco 托管服务通过 Git Hook 拒绝违规的 Push。

## 3. 绕过与审计 (Bypass & Audit)

我们必须承认，拥有 Git Write 权限的用户可以在 CLI 中绕过 Kanban 的 UI 限制。

- **应对策略**:
  - **审计日志**: Git Log 是不可篡改的证据。任何绕过 UI 的操作都会留下明确的 Commit 记录。
  - **软性约束**: 在企业环境中，通过“Git Log 审计”而非“绝对技术封锁”来管理通常更高效。
  - **硬性约束 (可选)**: 如果必须绝对控制，需使用服务端 Pre-receive Hook，这属于 Chassis/Git Server 的范畴，而非客户端的职责。

## 4. 总结

| 特性     | 物理层 (Layer 1)   | 策略层 (Layer 2)            |
| :------- | :----------------- | :-------------------------- |
| **依赖** | 仅 Git             | Git + SaaS/Server           |
| **身份** | Git Email          | SaaS Account (Linked Email) |
| **粒度** | 读/写 (二进制)     | 角色/动作 (细粒度)          |
| **适用** | 本地优先，去中心化 | 企业管控，流程合规          |
