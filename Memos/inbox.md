# Monoco Memos Inbox

## [5cec77] 2026-01-30 17:17:25
关于 Agent Hooks 的架构决策：1. 各 CLI 工具的 Agent Hooks 是私有特性，生态碎片化严重；2. Git Hooks 上下文不匹配，无法满足 Session 级别的清理需求；3. 必需设计 Monoco Native Hook System 以实现统一的生命周期管理。
