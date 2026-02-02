# Artifacts & Mailroom

Monoco Artifacts 系统提供了多模态产物的生命周期管理能力，包括：

1. **内容寻址存储 (CAS)**: 所有产物存储在全局池 `~/.monoco/artifacts` 中，基于内容的 SHA256 哈希值进行寻址和去重。
2. **自动化摄取 (Mailroom)**: 通过监听 `.monoco/dropzone/` 目录，自动触发文档（Office, PDF 等）到 WebP 的转换流程。
3. **环境追踪**: 自动探测系统中的 `LibreOffice`, `PyMuPDF` 等工具链。
4. **元数据管理**: 项目本地维护 `manifest.jsonl`，记录所有产物的类型、哈希及创建时间。

### 常用操作建议

- **上传文档**: 建议将原始文档放入 `.monoco/dropzone/`，等待 Mailroom 自动完成转换并注册为 Artifact。
- **查看产物**: 检查 `.monoco/artifacts/manifest.jsonl` 获取当前可用的产物列表。
- **引用产物**: 在多模态分析时，可以使用产物的 ID 或本地软链接路径。
