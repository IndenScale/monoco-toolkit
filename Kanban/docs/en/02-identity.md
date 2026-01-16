# Identity & Security

Monoco Kanban adopts a **"Physical Layer + Policy Layer"** dual-layer permission model, aiming to balance decentralized flexibility with enterprise-level control requirements.

## 1. Core Principles

> **Git Identity is the User Identity.**

We do not enforce a brand new account system. If Git recognizes your identity, Kanban recognizes your identity.

## 2. Layered Model

### Layer 1: The Physics

**Mechanism**: `Repo URL + Git Config (Email/Name)`

This is the basic operating mode of Kanban Desktop.

- **Authentication**:
  - Reads local `git config user.email` to determine current operator identity.
  - Relies on SSH Key / HTTPS Token to communicate with remote repository.
- **Authorization**:
  - **Read**: If you have Clone permission for the repo, you can view all tasks.
  - **Write**: If you have Push permission for the repo, you can modify all tasks.
- **Scenarios**: Individual developers, open source projects, small startups.

### Layer 2: The Policy

**Mechanism**: `SaaS Account + RBAC as Code`

When finer-grained permission control is needed (e.g., interns can only comment, not move cards), policies are superimposed via the SaaS layer.

- **Identity Binding**: User logs in to Monoco SaaS (GitHub/Google) and verifies ownership of their Git Email.
- **Policy File**: Permission rules are stored in the codebase (e.g., `.monoco/policy.yaml`), under Git version control.
  ```yaml
  roles:
    maintainer: ["alice@example.com"]
    guest: ["*@temp.com"]
  permissions:
    guest:
      - "issue:read"
      - "issue:comment"
      # Prohibit "issue:update_status"
  ```
- **Enforcement**:
  - **UI Layer**: Kanban parses policy file and disables specific buttons based on current user identity.
  - **Server Layer**: Monoco hosting service rejects violating Pushes via Git Hook.

## 3. Bypass & Audit

We must acknowledge that users with Git Write permission can bypass Kanban's UI restrictions via CLI.

- **Countermeasures**:
  - **Audit Logs**: Git Log is immutable evidence. Any operation bypassing UI leaves a clear Commit record.
  - **Soft Constraints**: In enterprise environments, managing via "Git Log Audit" rather than "Absolute Technical Blockade" is usually more efficient.
  - **Hard Constraints (Optional)**: If absolute control is mandatory, server-side Pre-receive Hooks should be used, which falls under Chassis/Git Server scope, not client responsibility.

## 4. Summary

| Feature | Physical Layer (Layer 1) | Policy Layer (Layer 2) |
| :--- | :--- | :--- |
| **Dependency** | Git Only | Git + SaaS/Server |
| **Identity** | Git Email | SaaS Account (Linked Email) |
| **Granularity** | Read/Write (Binary) | Role/Action (Fine-grained) |
| **Application** | Local First, Decentralized | Enterprise Control, Compliance |
