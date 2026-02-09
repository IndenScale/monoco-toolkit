---
id: FIX-0027
uid: 7a939a
type: fix
status: open
stage: review
title: 修复 doc-extractor 错误处理不完善导致残留不完整 blob 目录的问题
created_at: '2026-02-10T01:34:49'
updated_at: '2026-02-10T01:49:33'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0027'
files:
- .gitignore
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- src/monoco/features/doc_extractor/commands.py
- src/monoco/features/doc_extractor/extractor.py
- src/monoco/features/doc_extractor/models.py
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-10T01:34:49'
isolation:
  type: branch
  ref: FIX-0027-修复-doc-extractor-错误处理不完善导致残留不完整-blob-目录的问题
  created_at: '2026-02-10T01:34:54'
---

## FIX-0027: 修复 doc-extractor 错误处理不完善导致残留不完整 blob 目录的问题

## Objective
修复 doc-extractor 在转换失败时残留不完整 blob 目录的问题，确保失败时自动清理，并增强对不完整 blob 的检测能力。

## Acceptance Criteria
- [x] 使用事务式处理：先写入临时目录，成功后再原子移动到最终位置
- [x] 异常时自动清理临时目录，不残留不完整 blob
- [x] BlobRef.exists() 同时检查目录和 meta.json 存在性
- [x] 新增 `clean --incomplete` 命令清理残留的不完整 blob
- [x] 代码通过手动验证测试

## Technical Tasks
- [x] 重构 `_process_single()` 使用临时目录 + 原子移动
- [x] 修复 `BlobRef.exists()` 检测逻辑
- [x] 增强 `clean` 命令支持 `--incomplete` 选项
- [x] 验证修复效果

## Review Comments
- 修复采用事务式处理模式，确保原子性
- 已验证 BlobRef.exists() 正确识别不完整 blob
- 新增 clean --incomplete 命令便于运维清理
