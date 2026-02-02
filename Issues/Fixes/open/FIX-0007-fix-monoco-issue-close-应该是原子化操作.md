---
id: FIX-0007
uid: e492b4
type: fix
status: open
stage: review
title: 'Fix: monoco issue close 应该是原子化操作'
created_at: '2026-02-02T22:39:20'
updated_at: 2026-02-02 22:43:19
parent: EPIC-0000
dependencies: []
related: []
domains:
- Foundation
tags:
- '#EPIC-0000'
- '#FIX-0007'
files:
  - monoco/core/git.py
  - monoco/features/issue/commands.py
  - tests/features/issue/test_close_atomic.py
criticality: critical
solution: null
opened_at: '2026-02-02T22:39:20'
isolation:
  ref: branch:feat/FIX-0007-atomic-close
  type: branch
---

## FIX-0007: Fix: monoco issue close 应该是原子化操作

## Objective

### 问题背景
当前 `monoco issue close` 命令在执行过程中遇到错误时，**不会回滚已经执行的变更**，导致主线中产生脏数据。

### 实际案例（CHORE-0033 关闭过程）
1. 执行 `monoco issue close CHORE-0033 --solution implemented`
2. Smart Atomic Merge 成功执行，创建了提交 `262032f feat: atomic merge changes from CHORE-0033`
3. 后续操作遇到错误：`'str' object has no attribute 'value'`
4. **atomic merge 的提交仍然留在主线中**，没有回滚
5. 第二次运行时，系统检测到 "Atomic Merge Conflict"（因为两边都修改了文件）

### 期望行为
`monoco issue close` 应该是**原子化操作**：
- 所有步骤成功 → 提交所有变更
- 任何步骤失败 → 回滚所有变更，主线保持干净

## Acceptance Criteria
- [ ] `monoco issue close` 执行失败时，自动回滚所有已执行的变更
- [ ] 主线中不会出现部分完成的脏数据
- [ ] 错误信息清晰，告知用户操作已回滚
- [ ] 添加测试用例验证原子性行为

## Technical Tasks

### Phase 1: 问题分析与方案设计
- [x] 分析当前 close 命令的执行流程
- [x] 识别非原子化操作的具体位置
- [x] 设计原子化/事务机制（临时分支方案或 git reset 方案）

### Phase 2: 核心实现
- [x] 修改 `monoco/features/issue/commands.py` 中的 `move_close` 函数
- [x] 实现事务包装器：成功提交，失败回滚
- [x] 添加详细的错误处理和日志

### Phase 3: 测试与验证
- [x] 编写单元测试：模拟中间步骤失败，验证回滚行为
- [x] 集成测试：验证正常关闭流程不受影响
- [x] 手动测试：模拟各种错误场景

## Review Comments

### 2026-02-02
- 实现了原子化关闭操作，使用 git reset --hard 进行回滚
- 添加了详细的错误处理和回滚日志
- 编写了全面的测试用例验证原子性行为
- 所有测试通过
