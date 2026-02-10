---
id: FEAT-0198
uid: d7e728
type: feature
status: open
stage: doing
title: 实现 DingTalk 附件获取与存储系统
created_at: '2026-02-10T09:22:32'
updated_at: '2026-02-10T09:23:03'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0198'
files: []
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-10T09:22:32'
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

- [ ] DingTalk 消息中的附件能被正确识别和下载
- [ ] 附件存储在 `~/.monoco/dropbox/` 中，按 `{provider}/{date}/{message_id}/` 结构组织
- [ ] InboundMessage 的 artifacts 字段正确引用附件路径（相对 dropbox 根目录）
- [ ] `monoco mailbox list` 命令能显示附件信息
- [ ] 消息归档时附件一并移动到 archive/dropbox
- [ ] Artifact 模型新增 `url` 和 `downloaded_at` 字段

## Technical Tasks

### 1. DingTalk 附件获取功能
- [ ] 研究 DingTalk API 文件下载接口
- [ ] 在 `DingtalkAdapter._parse_payload()` 中解析消息中的附件信息
- [ ] 实现附件下载逻辑（调用 DingTalk API 获取文件内容）
- [ ] 支持多种附件类型：图片、文档、音频、视频等
- [ ] 在 `DingTalkStreamAdapter._parse_message()` 中同样实现附件解析
- [ ] 添加附件下载错误处理和重试机制

### 2. Artifact 模型增强
- [ ] 在 `schema.py` 中添加 `url: Optional[str]` 字段（原始下载链接）
- [ ] 添加 `downloaded_at: Optional[datetime]` 字段
- [ ] 更新 `Artifact.path` 字段描述，明确是相对于 dropbox 根目录的路径
- [ ] 更新相关文档（Mailbox Protocol Schema）

### 3. 附件存储目录实现
- [ ] 在 `constants.py` 中添加 `DROPBOX_DIR = "dropbox"`
- [ ] 创建全局附件存储目录 `~/.monoco/dropbox/`
- [ ] 设计子目录结构：`{provider}/{YYYYMMDD}/{message_id}/`
- [ ] 在 `MailboxStore` 中集成 dropbox 目录创建逻辑
- [ ] 实现附件文件的原子写入（先写临时文件再重命名）

### 4. Mail-Dropbox 引用机制
- [ ] 定义 `Artifact.path` 格式规范：`"dingtalk/20260210/dingtalk_abc123/screenshot.png"`
- [ ] 实现附件下载后更新 `InboundMessage.artifacts` 列表
- [ ] 在 `MailboxStore.create_inbound_message()` 中处理附件引用
- [ ] 在 Mailbox CLI 中支持附件列表展示（`monoco mailbox list --with-attachments`）
- [ ] 实现消息归档时附件一并移动到 `~/.monoco/dropbox/archive/`
- [ ] 添加附件存在性校验（文件是否存在、大小是否匹配）

### 5. 测试与验证
- [ ] 编写单元测试：附件下载逻辑
- [ ] 编写集成测试：完整的消息接收-附件下载-存储流程
- [ ] 测试多种文件类型（图片、PDF、压缩包等）
- [ ] 测试大文件下载和超时处理

## Dropbox 目录结构设计

```
~/.monoco/dropbox/
├── dingtalk/
│   ├── 20260210/
│   │   ├── dingtalk_msg_abc123/
│   │   │   ├── screenshot.png
│   │   │   └── document.pdf
│   │   └── dingtalk_msg_def456/
│   │       └── image.jpg
│   └── 20260211/
│       └── ...
├── lark/
│   └── ...
└── archive/
    └── dingtalk/
        └── ...
```

## Artifact Schema 更新

```python
class Artifact(BaseModel):
    """An attached artifact/file."""
    id: str = Field(..., description="Artifact ID (SHA256 hash)")
    name: str = Field(..., description="Original filename")
    type: ArtifactType = Field(..., description="Type of artifact")
    mime_type: Optional[str] = Field(None, description="MIME type")
    size: Optional[int] = Field(None, description="File size in bytes")
    path: str = Field(..., description="Path relative to ~/.monoco/dropbox/")
    url: Optional[str] = Field(None, description="Original download URL")
    downloaded_at: Optional[datetime] = Field(None, description="Download timestamp")
    inline: bool = Field(False, description="Whether this is an inline attachment")
```

## Related Files

- `src/monoco/features/courier/adapters/dingtalk.py`
- `src/monoco/features/courier/adapters/dingtalk_stream.py`
- `src/monoco/features/connector/protocol/schema.py`
- `src/monoco/features/connector/protocol/constants.py`
- `src/monoco/features/mailbox/store.py`
- `src/monoco/features/mailbox/commands.py`

## Dependencies

- DingTalk API 文件下载接口（需要调研）
- 可能需要新增 `aiofiles` 依赖用于异步文件操作

## References

- ADR-003: Mailbox Protocol Schema Specification
- Mailbox Protocol 文档（`docs/zh/04_Connectors/02_Mailbox_Protocol.md`）
