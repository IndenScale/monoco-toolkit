---
name: atom-knowledge
description: 知识管理的原子操作 - 捕获、处理、转化、归档
---

## 知识管理原子操作

知识管理的原子操作 - 捕获、处理、转化、归档

### 系统级合规规则

- Memo 是临时的，不应无限堆积
- 可执行的想法必须转为 Issue 追踪

### 操作定义

#### 1. 捕获 (capture)
- **描述**: 快速捕获 fleeting ideas
- **命令**: `monoco memo add <content>`
- **提醒**: 保持简洁，不中断当前工作流，添加上下文
- **检查点**:
  - 使用简洁的描述
  - 添加上下文（-c file:line 如适用）
  - 不中断当前任务流

#### 2. 处理 (process)
- **描述**: 定期处理 Memo，评估价值
- **命令**: `monoco memo list`
- **提醒**: 定期回顾和分类 Memo（建议每周）
- **检查点**:
  - 运行 monoco memo list 查看所有 Memo
  - 评估每个 Memo 的价值
  - 分类：可执行 / 纯参考 / 无价值

#### 3. 转化 (convert)
- **描述**: 将可执行的 Memo 转化为 Issue
- **命令**: `monoco issue create <type> -t <title>`
- **提醒**: 有价值的想法尽快转为 Issue
- **检查点**:
  - 判断 Issue 类型 (feature/chore/fix)
  - 编写清晰的描述和验收标准
  - 关联原始 Memo
- **合规规则**: 可执行的想法必须转为 Issue 追踪

#### 4. 归档 (archive)
- **描述**: 归档纯参考资料
- **提醒**: 纯参考资料归档保存，无价值的直接删除
- **检查点**:
  - 确认 Memo 内容为纯参考资料
  - 移动到知识库或文档
  - 从 Memo 列表中移除