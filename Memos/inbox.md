# Monoco Memos Inbox

## [f456df] 2026-01-29 17:11:09

Testing memo system from agent.

## [e43325] 2026-01-30 09:16:20

Issue 命令分支上下文检查规则讨论

提议规则：

1. monoco issue start/submit 必须在对应 issue 分支执行
2. monoco issue create/close 必须在 main 分支执行

合理性：

- 强制代码变更与 issue 关联
- 流程清晰：create → start (创建并切换到 issue 分支) → submit → switch to main → close
- 防止误操作

待考虑场景：

- start --no-branch 是否需要豁免
- 是否需要 --force 绕过检查
- workspace.yaml 是否可配置开关

建议：认同实施，添加配置选项

## [1a1263] 2026-01-30 14:13:24
> **Context**: `Quality Control`

改进点：monoco issue lint 应该检查并确保所有占位符（如 <- - pytest -q tests/integration/test_rpc_interface_evolution.py Required for Review/Done stage... -->）已被清除或替换，防止空内容提交。

## [f4abfc] 2026-01-30 14:13:59
> **Context**: `Quality Control`

改进点：monoco issue lint 应该检查并确保所有占位符（如 <- - pytest -q tests/integration/test_rpc_interface_evolution.py Required for Review/Done stage... -->）已被清除或替换，防止空内容提交。
