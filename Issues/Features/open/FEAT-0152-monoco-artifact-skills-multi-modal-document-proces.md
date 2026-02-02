---
id: FEAT-0152
uid: art_skill_01
type: feature
status: open
stage: review
title: 'Monoco Artifact Skills: Multi-modal Document Processing SOP'
created_at: '2026-02-02T00:00:00'
updated_at: '2026-02-02T09:07:27'
priority: high
parent: EPIC-0025
dependencies: []
related: []
domains:
- AgentEmpowerment
tags:
- '#EPIC-0025'
- '#FEAT-0152'
- skill
- sop
- documentation
files:
- monoco/features/artifact/resources/zh/skills/monoco_artifact/SKILL.md
- scripts/doc-to-webp.py
criticality: medium
isolation:
  type: branch
  ref: feat/feat-0152-monoco-artifact-skills-multi-modal-document-proces
  created_at: '2026-02-02T09:04:58'
owner: IndenScale
---

## FEAT-0152: Monoco Artifact Skills: Multi-modal Document Processing SOP

## 1. 背景与目标
在自动化程度达到 100% 之前，我们需要通过 **Agent Skill** 为智能体提供“处理二进制文档”的标准作业程序 (SOP)。本 Feature 旨在编写 `.agent/skills/artifact-docs.md`（及其关联脚本），指导 Agent 如何利用系统级工具执行 Office -> PDF -> WebP 的转换，并注册到 Monoco 产物系统中。

## 2. 核心内容
- **Environment Setup Guide**: 引导 Agent 探测或提示用户安装必要工具（如 LibreOffice）。
- **Conversion Workflow**: 定义标准的命令行调用序列及参数（如 DPI 设定、格式选择）。
- **Registry Instruction**: 指导 Agent 调用 Monoco CLI 或 API 将生成的图片注册为 Artifact。

## 3. 验收标准
- [x] **`.agent/skills/artifact-docs.md`**: 编写完成并包含清晰的转换步骤。
- [x] **Agent 验证**: 在 Pair 模式下，Agent 能够根据此 Skill 文档，利用宿主环境工具成功处理一个 docx 文件。
- [x] **异常处理建议**: 文档应包含字体缺失、转换锁死等常见问题的排查建议。

## 4. 技术任务
- [x] 调研并整理 LibreOffice Headless 转换的最佳实践参数。
- [x] 编写 Skill 文档中的 Prompt 模板。
- [x] 实现一个简单的辅助脚本 `scripts/doc-to-webp.py`（可选，供 Agent 调用）。

## 5. Review Comments
- [ ] 待评审。
