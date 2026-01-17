import * as vscode from "vscode";
import { ActionService, AgentAction } from "../services/ActionService";
import { AgentStateService } from "../services/AgentStateService";

export class ActionsTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<
    vscode.TreeItem | undefined | void
  > = new vscode.EventEmitter<vscode.TreeItem | undefined | void>();
  readonly onDidChangeTreeData: vscode.Event<
    vscode.TreeItem | undefined | void
  > = this._onDidChangeTreeData.event;

  constructor(
    private actionService: ActionService,
    private agentStateService: AgentStateService,
  ) {
    this.actionService.onDidChangeActions(() => this.refresh());
    this.agentStateService.onDidChangeState(() => this.refresh());
  }

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: vscode.TreeItem): Thenable<vscode.TreeItem[]> {
    if (!element) {
      return Promise.resolve([
        new vscode.TreeItem(
          "Actions",
          vscode.TreeItemCollapsibleState.Expanded,
        ),
        new vscode.TreeItem(
          "Providers",
          vscode.TreeItemCollapsibleState.Expanded,
        ),
      ]);
    }

    if (element.label === "Actions") {
      const actions = this.actionService.getActions();
      return Promise.resolve(actions.map((ex) => new ActionTreeItem(ex)));
    }

    if (element.label === "Providers") {
      const state = this.agentStateService.getState();
      if (!state) return Promise.resolve([]);

      const providers = state.providers || {};
      return Promise.resolve(
        Object.entries(providers).map(
          ([name, pState]) => new ProviderTreeItem(name, pState),
        ),
      );
    }

    return Promise.resolve([]);
  }
}

export class ActionTreeItem extends vscode.TreeItem {
  constructor(public readonly action: AgentAction) {
    super(action.name, vscode.TreeItemCollapsibleState.None);
    this.tooltip = action.description;
    this.description = action.description;
    this.contextValue = "action";
    this.iconPath = new vscode.ThemeIcon("sparkle");
    this.command = {
      command: "monoco.viewActionTemplate",
      title: "View Template",
      arguments: [action],
    };
  }
}

export class ProviderTreeItem extends vscode.TreeItem {
  constructor(
    public readonly name: string,
    public readonly state: any,
  ) {
    super(name, vscode.TreeItemCollapsibleState.None);
    this.description = state.available ? "Active" : "Inactive";
    this.tooltip =
      state.error ||
      (state.available ? `Path: ${state.path}` : "Provider not found");
    this.iconPath = new vscode.ThemeIcon(
      state.available ? "check" : "error",
      new vscode.ThemeColor(state.available ? "charts.green" : "charts.red"),
    );
    this.contextValue = "provider";
  }
}
