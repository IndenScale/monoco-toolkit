# Monoco Memos Inbox
## [844f87] 2026-02-01 21:14:28
> **Context**: `Post-Mortem`

复盘记录：
1. [Critical] 蜂群风暴：Daemon 调度器 Handover 策略引发无限 Agent 进程增殖，导致 OOM 崩溃。需增加冷却/退避机制。
2. [Docs] Context 缺失： 未说明 Memo 存储位置 ()，导致 Agent 无法正确定位文件。

## [325b48] 2026-02-01 21:35:48
> **Context**: `UX Feedback`

用户反馈：Issue 生命周期中的 'solution' 字段定义模糊。CLI 报错 'requires solution implemented' 但 issue update 命令并不支持 --solution 参数，导致通过命令行闭环困难。应明确它属 Front Matter 还是正文。

## [0c262b] 2026-02-01 21:37:06
> **Context**: `DevEx`

缺陷反馈：
1. [Template]  生成的 Markdown 模版 Front Matter 中缺失  字段默认值（应为  或占位），导致验证逻辑依赖隐式行为。
2. [CLI]  缺乏  参数接口，无法在不编辑文件的情况下满足 Close Policy (Requires solution='implemented')。
影响：阻碍了 Agent 通过纯 CLI 指令完成 Issue 闭环。
