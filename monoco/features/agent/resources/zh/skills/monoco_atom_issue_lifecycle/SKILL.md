---
name: atom-issue-lifecycle
description: Issue 生命周期管理的原子操作 - 创建、启动、提交、关闭工作单元
---

## Issue 生命周期管理原子操作

Issue 生命周期管理的原子操作 - 创建、启动、提交、关闭工作单元

### 系统级合规规则

- 禁止在 main/master 分支直接修改代码
- 必须使用 feature 分支进行开发
- 提交前必须通过 lint 检查
- 每个 Issue 必须至少包含 2 个 Checkbox
- Review/Done 阶段必须包含 Review Comments

### 操作定义

#### 1. 创建 (create)
- **描述**: 创建新的 Issue 工作单元
- **命令**: `monoco issue create <type> -t <title>`
- **提醒**: 选择合适的类型 (epic/feature/chore/fix)，编写清晰的描述
- **检查点**:
  - 必须包含至少 2 个 Checkbox
  - 标题必须与 Front Matter 一致

#### 2. 启动 (start)
- **描述**: 启动开发，创建功能分支
- **命令**: `monoco issue start <ID> --branch`
- **提醒**: 确保使用 --branch 创建功能分支，禁止在 main/master 上开发
- **检查点**:
  - 禁止在 main/master 分支直接修改代码
  - 必须创建 feature 分支

#### 3. 同步 (sync)
- **描述**: 同步文件追踪，记录修改的文件
- **命令**: `monoco issue sync-files`
- **提醒**: 定期同步文件追踪，保持 Issue 与代码变更同步

#### 4. 检查 (lint)
- **描述**: 检查 Issue 合规性
- **命令**: `monoco issue lint`
- **提醒**: 提交前必须运行 lint 检查
- **检查点**:
  - 必须通过所有合规检查

#### 5. 提交 (submit)
- **描述**: 提交代码进行评审
- **命令**: `monoco issue submit <ID>`
- **提醒**: 确保所有测试通过，lint 无错误后再提交
- **检查点**:
  - 所有单元测试必须通过
  - 必须通过 lint 检查

#### 6. 关闭 (close)
- **描述**: 关闭 Issue，清理环境
- **命令**: `monoco issue close <ID> --solution completed --prune`
- **提醒**: 代码合并后及时关闭 Issue，清理 feature 分支