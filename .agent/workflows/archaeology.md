---
description: 执行深度项目考古，追溯历史进展与架构演进。
---

# 项目考古工作流 (Project Archaeology)

该工作流用于在特定时间跨度内重构项目历史、识别关键里程碑并分析代码演化。由于涉及大规模的文件读取和日志分析，默认使用具有超大上下文窗口的 Gemini。

## 1. 配置参数
- **开始日期 (START_DATE)**: 调查起始时间 (例如: 2026-01-26)。
- **结束日期 (END_DATE)**: 调查截止时间 (例如: 2026-01-30)。
- **调查深度**: 建议读取 50-100 份以上相关文档。

## 2. 调度方式 (Dispatch)

使用以下标准指令调度考古智能体（Agent）：

// turbo
```bash
gemini -y -p "执行深度项目考古任务。
调查周期：从 {START_DATE} 到 {END_DATE}。
任务要求：
1. 深入分析 git log 和 git diff，确定该周期内的主要变更。
2. 广泛阅读受影响的文件及其上下文（目标 100 份文档）。
3. 识别并分类核心进展：Feature（功能实现）、Chore（工程维护）、Fix（缺陷修复）。
4. 分析关键的架构演进特征和决策点。
5. 生成深度调查报告（要求中文，5000-8000字以上）。
6. 报告路径：Archaeology/REPORT_{START_DATE}_{END_DATE}.md"
```

## 3. 约定与规范
- **分支规范**: 🛑 **禁止**使用 Feature 分支进行考古。所有考古报告应直接在主协作分支 (main) 上进行，以避免隔离导致的历史回溯偏差。
- **存储目录**: 所有报告必须存放在 `Archaeology/` 目录下。
- **命名规范**: `REPORT_YYYY_MM_DD_YYYY_MM_DD.md`。
- **报告结构**:
  - 执行摘要 (Executive Summary)
  - 关键事件时间线 (Timeline)
  - 核心模块演进分析 (Detailed Analysis)
  - 遗留问题与技术债 (Technical Debt)
  - 架构决策点分析 (ADR-like insights)
