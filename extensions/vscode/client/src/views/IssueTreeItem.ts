import * as vscode from "vscode";

/**
 * Issue data structure from LSP
 */
export interface Issue {
  id: string;
  title: string;
  type: "epic" | "arch" | "feature" | "chore" | "fix" | "bug";
  status: "open" | "closed" | "backlog";
  stage: "draft" | "doing" | "review" | "done";
  parent?: string;
  path?: string;
  project_id?: string;
  tags?: string[];
  children?: Issue[];
}

/**
 * TreeItem for Issue display in native TreeView
 */
export class IssueTreeItem extends vscode.TreeItem {
  constructor(
    public readonly issue: Issue,
    public readonly childCount: number = 0,
    collapsibleState: vscode.TreeItemCollapsibleState = vscode
      .TreeItemCollapsibleState.None,
  ) {
    super(issue.title, collapsibleState);

    // Set context value for conditional commands
    this.contextValue = `issue-${issue.type}`;

    // Set tooltip
    this.tooltip = this.buildTooltip();

    // Set description (right-aligned text)
    this.description = this.buildDescription();

    // Set icon based on stage
    this.iconPath = this.getStageIcon();

    // Enable drag and drop
    this.resourceUri = issue.path ? vscode.Uri.file(issue.path) : undefined;

    // Double-click opens the file
    if (issue.path) {
      if (issue.type === "epic" || issue.type === "arch") {
        this.command = {
          command: "monoco.openIssueAndExpand",
          title: "Open Issue and Expand",
          arguments: [this], // Pass self for reveal
        };
      } else {
        this.command = {
          command: "vscode.open",
          title: "Open Issue",
          arguments: [vscode.Uri.file(issue.path)],
        };
      }
    }
  }

  /**
   * Build tooltip with issue details
   */
  private buildTooltip(): vscode.MarkdownString {
    const md = new vscode.MarkdownString();
    md.appendMarkdown(`**${this.issue.id}**: ${this.issue.title}\n\n`);
    md.appendMarkdown(`- **Type**: ${this.issue.type}\n`);
    md.appendMarkdown(`- **Status**: ${this.issue.status}\n`);
    md.appendMarkdown(`- **Stage**: ${this.issue.stage}\n`);
    if (this.issue.tags && this.issue.tags.length > 0) {
      md.appendMarkdown(`- **Tags**: ${this.issue.tags.join(", ")}\n`);
    }
    if (this.issue.path) {
      md.appendMarkdown(`\n📄 ${this.issue.path}`);
    }
    return md;
  }

  /**
   * Build description (right-aligned text)
   * Shows child count badge if has children
   */
  private buildDescription(): string {
    const parts: string[] = [];

    // Child count badge (like webview bubble)
    if (this.childCount > 0) {
      parts.push(`${this.childCount > 99 ? "99+" : this.childCount}`);
    }

    return parts.join(" ");
  }

  /**
   * Get icon based on stage with color
   */
  private getStageIcon(): vscode.ThemeIcon {
    const stageColorMap: Record<string, string> = {
      draft: "descriptionForeground", // Gray
      doing: "charts.blue", // Blue
      review: "charts.purple", // Purple
      done: "charts.green", // Green
    };

    const typeIconMap: Record<string, string> = {
      epic: "symbol-namespace",
      arch: "symbol-structure",
      feature: "symbol-method",
      chore: "tools",
      fix: "bug",
      bug: "bug",
    };

    const iconName = typeIconMap[this.issue.type] || "symbol-misc";
    const color = stageColorMap[this.issue.stage] || "descriptionForeground";

    return new vscode.ThemeIcon(iconName, new vscode.ThemeColor(color));
  }
}
