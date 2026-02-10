# Artifacts

Monoco Artifacts 系统提供了多模态产物的生命周期管理能力，基于内容寻址存储 (CAS) 实现。

## 核心功能

1. **内容寻址存储 (CAS)**: 所有产物存储在全局池 `~/.monoco/artifacts` 中，基于内容的 SHA256 哈希值进行寻址和去重。
2. **元数据管理**: 项目本地维护 `manifest.jsonl`，记录所有产物的类型、哈希及创建时间。

## 常用操作

- **查看产物**: 检查 `.monoco/artifacts/manifest.jsonl` 获取当前可用的产物列表。
- **引用产物**: 在多模态分析时，可以使用产物的 ID 或本地软链接路径。
