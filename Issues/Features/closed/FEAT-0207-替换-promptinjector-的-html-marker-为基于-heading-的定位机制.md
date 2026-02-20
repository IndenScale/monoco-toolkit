---
id: FEAT-0207
uid: ced828
type: feature
status: open
stage: review
title: 使用 mdp CLI 工具替换 PromptInjector 的 HTML marker 机制
created_at: '2026-02-20T20:29:53'
updated_at: '2026-02-20T20:35:56'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0207'
files: []
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-20T20:29:53'
---

## FEAT-0207: 使用 mdp CLI 工具替换 PromptInjector 的 HTML marker 机制

## Objective
<!-- Describe the "Why" and "What" clearly. Focus on value. -->

当前 `PromptInjector` 类（`src/monoco/core/injection.py`）使用 HTML 注释作为 marker 来定位和管理 AGENTS.md 中的自动生成内容：

```python
MANAGED_START = "<!-- MONOCO_GENERATED_START -->"
MANAGED_END = "<!-- MONOCO_GENERATED_END -->"
```

这种方式存在以下问题：
1. **视觉噪音**：HTML 注释在 markdown 源文件中显得杂乱
2. **不符合 markdown 语义**：HTML 注释是通用标记，不具备 markdown 的结构性
3. **需要自行实现复杂的定位逻辑**：`PromptInjector` 需要处理 header demoting、内容合并等逻辑
4. **与现有工具重复**：mdp (md-patch) 工具已经提供了成熟的 heading-based markdown 编辑能力

本 Issue 的目标是将 `PromptInjector` 的实现从基于 HTML marker 的自定义逻辑，迁移为直接调用 `mdp` CLI 工具，利用其声明式、幂等的 markdown 块修补能力。

## Acceptance Criteria
<!-- Define binary conditions for success. -->
- [ ] `PromptInjector` 不再使用 `<!-- MONOCO_GENERATED_START/END -->` HTML 注释 marker
- [ ] 使用 `mdp patch` 命令在 `## Monoco` heading 后追加/替换内容
- [ ] 支持批量操作时使用 `mdp plan` + `mdp apply`
- [ ] 保留向后兼容：能正确处理旧的带 HTML marker 的文件（可选：提供迁移命令）
- [ ] 更新 `AGENTS.md`、`GEMINI.md`、`CLAUDE.md` 等文件，移除 HTML marker
- [ ] 所有现有测试通过，并添加新测试验证 mdp 集成
- [ ] 文档更新：说明需要安装 mdp 工具

## Technical Tasks
<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

<!-- Status Syntax: -->
<!-- [ ] To Do -->
<!-- [/] Doing -->
<!-- [x] Done -->
<!-- [~] Cancelled -->
<!-- [ ] Parent Task -->
<!--   - [ ] Sub Task -->

- [ ] 调研 mdp CLI 的集成方式
  - [ ] 确认 mdp 的安装位置（`~/.local/bin/mdp`）
  - [ ] 验证 `mdp patch -f AGENTS.md -H "## Monoco" -i 0 --op append -c "内容"` 的行为
  - [ ] 验证 `mdp plan` + `mdp apply` 的批量操作模式
  
- [ ] 重构 `PromptInjector` 类
  - [ ] 移除 `MANAGED_START` 和 `MANAGED_END` HTML marker 常量
  - [ ] 保留 `MANAGED_HEADER = "## Monoco"` 作为目标 heading
  - [ ] 实现 `inject()` 方法：生成临时 YAML 配置，调用 `mdp apply`
  - [ ] 实现 `remove()` 方法：调用 `mdp patch --op delete`
  - [ ] 处理 mdp 执行错误和返回值
  
- [ ] 实现内容生成逻辑
  - [ ] 保留 header level 自动降级逻辑（在调用 mdp 前处理内容）
  - [ ] 保留文件头注释生成（可选：移到 mdp 外部处理）
  - [ ] 生成符合 mdp 格式的 YAML 配置
  
- [ ] 向后兼容（可选）
  - [ ] 检测文件中是否存在旧的 HTML marker
  - [ ] 提供 `monoco sync --migrate` 选项自动清理旧 marker
  
- [ ] 更新受影响的文件
  - [ ] 更新 `AGENTS.md`，移除 HTML marker，确保 `## Monoco` heading 存在
  - [ ] 更新 `GEMINI.md`，移除 HTML marker
  - [ ] 更新 `CLAUDE.md`，移除 HTML marker
  
- [ ] 更新测试
  - [ ] 更新 `tests/core/test_injector.py` 中的测试用例
  - [ ] Mock `subprocess.run` 验证 mdp 调用参数
  - [ ] 添加集成测试（如果环境允许）
  - [ ] 确保所有测试通过
  
- [ ] 文档和配置
  - [ ] 在 `pyproject.toml` 或文档中说明 mdp 依赖
  - [ ] 更新 `AGENTS.md` 中的相关文档（如果提到了实现细节）
  - [ ] 更新代码注释和 docstring

## References

### mdp CLI 用法参考

```bash
# 单文件操作
mdp patch -f doc.md -H "## Monoco" -i 0 --op append -c "新增内容" --force

# 批量操作
mdp plan patches.yaml    # 预览
mdp apply patches.yaml --force   # 应用
```

### patches.yaml 格式示例

```yaml
operations:
  - file: AGENTS.md
    heading:
      - "## Monoco"
    index: 0
    operation: replace
    content: |
      > **Auto-Generated**: This section is managed by Monoco.
      
      ### Agent
      ...
```

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
