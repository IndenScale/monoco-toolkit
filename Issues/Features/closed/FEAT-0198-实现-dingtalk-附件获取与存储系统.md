---
id: FEAT-0198
uid: d7e728
type: feature
status: closed
stage: done
title: 实现 DingTalk 附件获取与存储系统
created_at: '2026-02-10T09:22:32'
updated_at: '2026-02-10T11:19:51'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0198'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- src/monoco/features/artifact/store.py
- src/monoco/features/connector/protocol/constants.py
- src/monoco/features/connector/protocol/schema.py
- src/monoco/features/courier/adapters/dingtalk.py
- src/monoco/features/courier/adapters/dingtalk_artifacts.py
- src/monoco/features/courier/adapters/dingtalk_stream.py
- src/monoco/features/mailbox/commands.py
- src/monoco/features/mailbox/models.py
- src/monoco/features/mailbox/queries.py
- src/monoco/features/mailbox/store.py
- tests/features/courier/test_dingtalk_stream.py
- tests/integration/test_dingtalk_artifact_integration.py
- tests/unit/test_artifact_store.py
criticality: medium
solution: implemented
opened_at: '2026-02-10T09:22:32'
closed_at: '2026-02-10T10:13:23'
---

## FEAT-0198: 实现 DingTalk 附件获取与存储系统

## Objective

实现对 DingTalk 消息的附件完整支持，包括下载、存储和引用机制。

基于调查发现，当前系统：
- Artifact 数据模型已定义，但适配器未实现附件获取（`artifacts=[],  # TODO: Handle file attachments`）
- 文档设计了 `~/.monoco/dropzone/` 附件存储目录，但代码未定义相关常量
- Artifact.path 字段描述模糊，缺乏明确的引用规范

本 Issue 旨在完成附件功能的端到端实现。

## Acceptance Criteria

- [x] DingTalk 消息中的附件能被正确识别和下载
- [x] 附件存储在 `~/.monoco/artifacts/` 中，使用内容寻址扁平结构
- [x] InboundMessage 的 artifacts 字段正确引用附件路径（文件名即短 hash）
- [x] `monoco mailbox list` 命令能显示附件信息
- [x] 消息归档时消息文件移动，artifacts 保持原位（内容寻址共享）
- [x] Artifact 模型新增 `url` 和 `downloaded_at` 字段

## Technical Tasks

### 1. DingTalk 附件获取功能
- [x] 研究 DingTalk API 文件下载接口
- [x] 在 `DingtalkAdapter._parse_payload()` 中解析消息中的附件信息
- [x] 实现附件下载逻辑（调用 DingTalk API 获取文件内容）
- [x] 支持多种附件类型：图片、文档、音频、视频等
- [x] 在 `DingTalkStreamAdapter._parse_message()` 中同样实现附件解析
- [x] 添加附件下载错误处理和重试机制

### 2. Artifact 模型增强
- [x] 在 `schema.py` 中添加 `url: Optional[str]` 字段（原始下载链接）
- [x] 添加 `downloaded_at: Optional[datetime]` 字段
- [x] 更新 `Artifact.path` 字段描述，明确是相对于 artifacts 目录的文件名
- [x] 更新相关文档（Mailbox Protocol Schema）

### 3. 附件存储目录实现 (Content-Addressed Storage)
- [x] 在 `constants.py` 中添加 `ARTIFACTS_DIR = "artifacts"`
- [x] 创建 ArtifactStore 模块实现内容寻址存储
- [x] 设计扁平结构：文件名为 `{short_hash}{ext}`（如 `a1b2c3d4.png`）
- [x] 使用 `manifest.jsonl` 记录元数据（原始文件名、来源消息等）
- [x] 实现附件文件的原子写入（先写临时文件再重命名）
- [x] 自动去重：相同内容 = 相同 hash = 同一文件

### 4. Artifact 引用机制
- [x] 定义 `Artifact.path` 格式规范：`"a1b2c3d4.png"`（短 hash + 扩展名）
- [x] 实现附件下载后更新 `InboundMessage.artifacts` 列表
- [x] 在 `MailboxStore.create_inbound_message()` 中处理附件引用
- [x] 在 Mailbox CLI 中支持附件列表展示（`monoco mailbox list --with-attachments`）
- [x] 消息归档时 artifacts 保持原位（可能被多消息引用）
- [x] 添加附件存在性校验（通过 ArtifactStore.validate）

### 5. 测试与验证
- [x] 编写单元测试：ArtifactStore 核心功能
- [x] 编写单元测试：附件下载逻辑
- [x] 编写集成测试：完整的消息接收-附件下载-存储流程
- [x] 测试多种文件类型（图片、PDF、压缩包等）
- [x] 测试大文件下载和超时处理

## Artifacts 目录结构设计 (Content-Addressed)

```
~/.monoco/artifacts/
├── a1b2c3d4.png          # 图片附件（短 hash = SHA256 前 8 位）
├── e5f6g7h8.pdf          # PDF 文档
├── i9j0k1l2.jpg          # 另一张图片
└── manifest.jsonl        # 元数据索引（append-only）
```

### manifest.jsonl 格式

```jsonl
{"hash": "a1b2c3d4e5f6...", "short_hash": "a1b2c3d4", "name": "screenshot.png", "message_id": "dingtalk_abc123", "provider": "dingtalk", "size": 1024, "mime_type": "image/png", "downloaded_at": "2026-02-10T09:30:00Z", "url": "https://..."}
{"hash": "e5f6g7h8i9j0...", "short_hash": "e5f6g7h8", "name": "doc.pdf", "message_id": "dingtalk_def456", "provider": "dingtalk", "size": 2048, "mime_type": "application/pdf", "downloaded_at": "2026-02-10T09:35:00Z", "url": "https://..."}
```

## 设计决策记录

### 为什么使用 Content-Addressed Storage？

1. **天然去重**：相同文件只存储一次，节省空间
2. **跨消息复用**：同一文件可被多消息引用，无需复制
3. **数据完整性**：hash 校验确保文件未被篡改
4. **简化归档**：消息归档时无需移动大文件

### 为什么扁平结构而非层级目录？

1. **简化查找**：hash 即路径，O(1) 访问
2. **避免嵌套**：无需管理深层目录树
3. **Git 风格**：类似 Git objects 存储设计

## Artifact Schema 更新

```python
class Artifact(BaseModel):
    """An attached artifact/file."""
    id: str = Field(..., description="Artifact ID (SHA256 hash)")
    name: str = Field(..., description="Original filename")
    type: ArtifactType = Field(..., description="Type of artifact")
    mime_type: Optional[str] = Field(None, description="MIME type")
    size: Optional[int] = Field(None, description="File size in bytes")
    path: str = Field(..., description="Filename in ~/.monoco/artifacts/ (short_hash + ext)")
    url: Optional[str] = Field(None, description="Original download URL")
    downloaded_at: Optional[datetime] = Field(None, description="Download timestamp")
    inline: bool = Field(False, description="Whether this is an inline attachment")
```

## Related Files

- `src/monoco/features/connector/protocol/schema.py` - Artifact 模型定义
- `src/monoco/features/connector/protocol/constants.py` - ARTIFACTS_DIR 常量
- `src/monoco/features/artifact/store.py` - 内容寻址存储实现（新增）
- `src/monoco/features/courier/adapters/dingtalk.py` - DingTalk 适配器
- `src/monoco/features/courier/adapters/dingtalk_stream.py` - DingTalk Stream 适配器
- `src/monoco/features/courier/adapters/dingtalk_artifacts.py` - 附件下载器（新增）
- `src/monoco/features/mailbox/store.py` - Mailbox 存储
- `src/monoco/features/mailbox/commands.py` - CLI 命令
- `src/monoco/features/mailbox/models.py` - MessageListItem 模型
- `src/monoco/features/mailbox/queries.py` - 查询引擎

## Dependencies

- 使用现有 `httpx` 依赖进行异步 HTTP 下载
- 无需新增依赖

## References

- ADR-003: Mailbox Protocol Schema Specification
- Mailbox Protocol 文档（`docs/zh/04_Connectors/02_Mailbox_Protocol.md`）

## Review Comments

### Self Review (2026-02-10)

**验收结果**: ✅ 通过

**完成情况**:
1. ✅ DingTalk 消息中的附件能被正确识别和下载
2. ✅ 附件存储在 `~/.monoco/artifacts/` 中，使用内容寻址扁平结构
3. ✅ InboundMessage 的 artifacts 字段正确引用附件路径（文件名即短 hash）
4. ✅ `monoco mailbox list` 命令能显示附件信息
5. ✅ 消息归档时消息文件移动，artifacts 保持原位（内容寻址共享）
6. ✅ Artifact 模型新增 `url` 和 `downloaded_at` 字段

**测试覆盖**:
- ✅ 单元测试：ArtifactStore 核心功能（tests/unit/test_artifact_store.py）
- ✅ 单元测试：DingTalk Stream 适配器（tests/features/courier/test_dingtalk_stream.py）
- ✅ 集成测试：完整的消息接收-附件下载-存储流程（tests/integration/test_dingtalk_artifact_integration.py）
- ✅ 测试多种文件类型：图片、文档、音频、视频、压缩包、代码文件
- ✅ 测试错误处理：超时、HTTP 错误、空内容、网络错误
- ✅ 测试大文件下载（10MB 模拟）
- ✅ 测试内容去重功能

**代码质量**:
- 所有 63 个测试通过
- 代码遵循项目架构规范
- 错误处理完善，使用日志记录异常
- 异步操作正确处理
