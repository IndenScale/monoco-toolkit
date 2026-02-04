---
id: FIX-0012
uid: b99df3
type: fix
status: closed
stage: done
title: 修复 sync-files 中 Git 路径转义导致的 close 失败
created_at: '2026-02-04T10:42:32'
updated_at: '2026-02-04T11:04:51'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0012'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Fixes/open/FIX-0012-修复-sync-files-中-git-路径转义导致的-close-失败.md
- monoco/features/issue/core.py
- tests/features/issue/test_git_path_unquote.py
criticality: high
solution: implemented
opened_at: '2026-02-04T10:42:32'
closed_at: '2026-02-04T11:04:51'
isolation:
  type: branch
  ref: feat/fix-0012-修复-sync-files-中-git-路径转义导致的-close-失败
  created_at: '2026-02-04T11:00:05'
---

## FIX-0012: 修复 sync-files 中 Git 路径转义导致的 close 失败

## Objective

### 问题描述

当 Issue 的标题包含非 ASCII 字符（如中文）时，`monoco issue close` 命令会因 Git 路径转义问题而失败。

### 错误现象

```
Error: Merge Error: Selective checkout failed: Failed to checkout files from
feat/feat-0165-xxx: error: pathspec
'"Issues/Features/open/FEAT-XXXX-\351\207\215..."' did not match any file(s) known to git
```

### 根本原因

1. **`sync_issue_files` 存储转义路径**: 当调用 `git diff --name-only` 获取变更文件时，Git 对非 ASCII 文件名使用 **C-quoting 格式**（如 `"Issues/path-\351\207\215.md"`）
2. **未解码直接存入 YAML**: `core.py:1332` 直接将带引号和转义的路径存入 `files` 字段
3. **`close` 使用转义路径**: `merge_issue_changes` 将转义路径传给 `git checkout`，导致文件找不到

### 预期行为

- `sync-files` 应存储可读的原生路径（如 `Issues/Features/.../FEAT-XXXX-中文标题.md`）
- `close` 应能正确检出这些文件，不受字符编码影响

## Acceptance Criteria
<!-- Define binary conditions for success. -->
- [x] 创建 `_unquote_git_path()` 函数解码 Git C-quoting 格式（双引号包裹 + 八进制转义）
- [x] 在 `sync_issue_files()` 中调用解码函数，确保 `files` 字段存储原生路径
- [x] 在 `merge_issue_changes()` 中处理已存在的历史转义路径（兼容性）
- [x] 添加单元测试验证中文、空格等特殊字符路径的编解码
- [x] 通过 `monoco issue lint` 验证修复后的问题单格式正确

## Technical Tasks

### Phase 1: 核心修复

- [x] 在 `monoco/features/issue/core.py` 添加 `_unquote_git_path()` 辅助函数
  - [x] 实现移除首尾双引号 `"..."`
  - [x] 实现八进制转义解码 `\351\207\215` → `重`
  - [x] 处理边界情况（无引号、已解码路径等）
- [x] 修改 `sync_issue_files()` (core.py:1332)
  - [x] 对 `git diff` 输出的每个路径调用 `_unquote_git_path()`
  - [x] 确保排序前已完成解码

### Phase 2: 兼容性处理

- [x] 修改 `merge_issue_changes()` (core.py:1449-1453)
  - [x] 检出文件前检查路径是否仍为转义格式
  - [x] 如有需要，解码后尝试检出
- [x] 更新 `find_issue_path_across_branches()` 中的路径处理（如适用）

### Phase 3: 测试与验证

- [x] 在 `tests/features/issue/` 添加测试文件
  - [x] 测试 `_unquote_git_path()` 的各种输入
    - [x] 标准 ASCII 路径（无变化）
    - [x] 中文路径 `"path-\351\207\215.md"` → `path-重.md`
    - [x] 空格路径 `"path\ with\ space.md"` → `path with space.md`
    - [x] 已解码路径（无引号，无变化）
- [x] 手动验证修复流程
  - [x] 创建含中文标题的 Feature
  - [x] 执行 `sync-files` 验证 YAML 存储格式
  - [x] 执行 `close` 验证能成功完成

## Review Comments

### 根因分析（详细）

#### Git C-quoting 格式

Git 在遇到非 ASCII 字符时使用 C 风格的转义：

```bash
$ git diff --name-only main...feat-branch
"Issues/Features/open/FEAT-XXXX-\351\207\215\346\236\204-memo-inbox-\344\270\272\344\277\241\345\217\267\351\230\237\345\210\227\346\250\241\345\236\213-\346\266\210\350\264\271\345\215\263\351\224\200\346\257\201.md"
```

这包含：
1. 外层双引号 `"..."`
2. 八进制转义 `\351\207\215` 表示 UTF-8 字节 `E9 87 8D`（字符 `重`）

#### 代码问题定位

**`core.py:1332` - sync_issue_files**:
```python
changed_files = [f.strip() for f in stdout.splitlines() if f.strip()]
# 直接存储，未解码转义字符
```

**`core.py:1451` - merge_issue_changes**:
```python
git.git_checkout_files(project_root, source_ref, issue.files)
# 转义路径直接传给 git checkout，导致 "pathspec did not match"
```

#### 解码算法参考

```python
def _unquote_git_path(path: str) -> str:
    path = path.strip()
    if path.startswith('"') and path.endswith('"'):
        path = path[1:-1]
        import re
        def decode_octal(m):
            return chr(int(m.group(1), 8))
        path = re.sub(r'\\(\d{3})', decode_octal, path)
    return path
```

### 影响范围

- **高**: 所有含非 ASCII 字符（中文、日文、emoji 等）的 Issue 标题
- **中**: 含空格的文件路径（Git 默认也会引用）
- **低**: 纯 ASCII 路径（无影响）

## Review Comments

### 实现总结

**修复方案**:
1. **添加 `_unquote_git_path()` 函数** (`core.py:86-134`):
   - 检测双引号包裹的 C-quoting 格式
   - 将八进制转义序列 (`\351\207\215`) 解析为字节
   - 使用 UTF-8 解码字节序列为 Unicode 字符串

2. **修改 `sync_issue_files()`** (`core.py:1336-1338`):
   - 在存储 `files` 字段前调用 `_unquote_git_path()` 解码路径
   - 确保 YAML 中存储的是可读的原生路径

3. **修改 `merge_issue_changes()`** (`core.py:1425-1427`, `1441-1445`):
   - 使用 `decoded_files` 变量兼容历史转义路径
   - 冲突检测和选择性检出均使用解码后的路径

**验证结果**:
- 15 个单元测试全部通过
- `monoco issue lint` 检查通过
- `sync-files` 成功存储中文路径到 YAML

**边界情况处理**:
- ASCII 路径（无引号）: 保持不变
- 已解码路径: 保持不变（无二次解码）
- 混合内容（中文+空格）: 正确解码
- 空字符串/空白字符: 安全处理
