/* eslint-disable @typescript-eslint/naming-convention */
import * as vscode from 'vscode'

export const FILTER_TYPES = {
  ALL: 'all',
  MY_ISSUES: 'my_issues',
  PROJECT: 'project',
  STATUS: 'status',
}

export class FilterItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly type: string,
    public readonly value?: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState = vscode
      .TreeItemCollapsibleState.None
  ) {
    super(label, collapsibleState)
    if (type === FILTER_TYPES.PROJECT) {
      this.iconPath = new vscode.ThemeIcon('folder')
      this.contextValue = 'project-filter'
    } else if (type === FILTER_TYPES.STATUS) {
      this.iconPath = new vscode.ThemeIcon('circle-outline')
    } else {
      this.iconPath = new vscode.ThemeIcon('filter')
    }
  }
}

export class IssueFilterProvider implements vscode.TreeDataProvider<FilterItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<FilterItem | undefined | void>()
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event

  private projects: string[] = []

  constructor() {}

  refresh(): void {
    this._onDidChangeTreeData.fire()
  }

  setProjects(projects: string[]) {
    this.projects = projects
    this.refresh()
  }

  getTreeItem(element: FilterItem): vscode.TreeItem {
    return element
  }

  getChildren(element?: FilterItem): vscode.ProviderResult<FilterItem[]> {
    if (!element) {
      return [
        new FilterItem('All Issues', FILTER_TYPES.ALL, 'all'),
        // new FilterItem("My Issues", FILTER_TYPES.MY_ISSUES, "my_issues"), // Future feature
        new FilterItem(
          'Projects',
          FILTER_TYPES.PROJECT,
          undefined,
          vscode.TreeItemCollapsibleState.Expanded
        ),
      ]
    }

    if (element.label === 'Projects') {
      if (this.projects.length === 0) {
        return [new FilterItem('No Projects Found', 'info')]
      }
      return [
        new FilterItem('All Projects', FILTER_TYPES.PROJECT, 'all'),
        new FilterItem('Root Workspace', FILTER_TYPES.PROJECT, 'root'),
        ...this.projects.map((p) => new FilterItem(p, FILTER_TYPES.PROJECT, p)),
      ]
    }

    return []
  }
}
