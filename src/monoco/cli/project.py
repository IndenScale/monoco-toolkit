import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
import yaml

from monoco.core.workspace import find_projects
from monoco.core.output import AgentOutput, OutputManager

app = typer.Typer(help="Manage Monoco Projects")
console = Console()

# Article template content for spike system
ARTICLE_TEMPLATE = '''---
# ===== 身份标识 =====
id: "UNKNOWN"                       # 必填：全局唯一标识符（kebab-case）
title: "UNKNOWN"                    # 必填：文章标题

# ===== 来源信息 =====
source: "UNKNOWN"                   # 必填：原始 URL（不知道填 UNKNOWN）
date: "UNKNOWN"                     # 必填：发布日期 ISO 8601（不知道填 UNKNOWN）
author: "UNKNOWN"                   # 可选：作者

# ===== 类型分类 =====
# 必填：article | paper | report | doc | blog | video
type: "UNKNOWN"

# ===== 国际化 =====
language: "UNKNOWN"                 # 可选：en | zh | ja
translations:                       # 可选：翻译版本映射
  # zh: "./zh/UNKNOWN.md"

# ===== 知识治理 =====
company: "UNKNOWN"                  # 可选：所属公司/组织
domain:                             # 可选：领域分类（数组）
  # - "UNKNOWN"
tags:                               # 可选：自由标签（数组）
  # - "UNKNOWN"

# ===== 关联知识 =====
related_repos:                      # 可选：关联的代码仓库
  # - "UNKNOWN"
related_articles:                   # 可选：关联的其他文章
  # - "UNKNOWN"

# ===== 内容摘要（用于 RAG）=====
summary: |
  UNKNOWN
---

# 正文从这里开始

## 填写指南

1. **UNKNOWN 占位符**：所有字段默认 UNKNOWN，不确定就保留 UNKNOWN
2. **必填字段**：id, title, source, date, type 必须替换为实际值或保持 UNKNOWN
3. **可选字段**：不知道就保留 UNKNOWN 或删除整行
4. **后续补充**：运行 `monoco spike lint` 会列出所有 UNKNOWN 字段

## 内容规范

- 保持原始内容完整性
- 可以添加自己的笔记和批注，使用引用格式：
  > 我的批注：这个观点很有启发性
- 使用相对路径引用同目录下的图片
  ![alt](./images/diagram.png)

## i18n 翻译

如需创建翻译版本：
1. 创建 `zh/` 子目录（对应 language 代码）
2. 复制本文档到 `zh/article-name.md`
3. 更新 `language` 字段为 "zh"
4. 更新主文档的 `translations.zh` 指向翻译文件
'''


@app.command("list")
def list_projects(
    json: AgentOutput = False,
    root: Optional[str] = typer.Option(None, "--root", help="Workspace root"),
):
    """List all discovered projects in the workspace."""
    cwd = Path(root).resolve() if root else Path.cwd()
    projects = find_projects(cwd)

    if OutputManager.is_agent_mode():
        data = [
            {
                "id": p.id,
                "name": p.name,
                "path": str(p.path),
                "key": p.config.project.key if p.config.project else "",
            }
            for p in projects
        ]
        OutputManager.print(data)
    else:
        table = Table(title=f"Projects in {cwd}")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Key", style="green")
        table.add_column("Path", style="dim")

        for p in projects:
            path_str = (
                str(p.path.relative_to(cwd))
                if p.path.is_relative_to(cwd)
                else str(p.path)
            )
            if path_str == ".":
                path_str = "(root)"
            key = p.config.project.key if p.config.project else "N/A"
            table.add_row(p.id, p.name, key, path_str)

        console.print(table)


@app.command("init")
def init_project(
    name: str = typer.Option(..., "--name", "-n", help="Project Name"),
    key: str = typer.Option(..., "--key", "-k", help="Project Key"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing config"
    ),
    json: AgentOutput = False,
):
    """Initialize a new project in the current directory."""
    cwd = Path.cwd()
    project_config_path = cwd / ".monoco" / "project.yaml"

    if project_config_path.exists() and not force:
        OutputManager.error(
            f"Project already initialized in {cwd}. Use --force to overwrite."
        )
        raise typer.Exit(code=1)

    cwd.mkdir(parents=True, exist_ok=True)
    (cwd / ".monoco").mkdir(exist_ok=True)

    # Create .references directory structure and inject article template
    refs_dir = cwd / ".references"
    articles_dir = refs_dir / "articles"
    template_path = articles_dir / "template.md"

    articles_dir.mkdir(parents=True, exist_ok=True)

    # Inject article template if it doesn't exist or force is True
    if not template_path.exists() or force:
        with open(template_path, "w") as f:
            f.write(ARTICLE_TEMPLATE)

    config = {"project": {"name": name, "key": key}}

    with open(project_config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    OutputManager.print(
        {
            "status": "initialized",
            "name": name,
            "key": key,
            "path": str(cwd),
            "config_file": str(project_config_path),
            "template_file": str(template_path),
        }
    )
