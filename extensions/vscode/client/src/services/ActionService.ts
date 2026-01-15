import * as vscode from "vscode";
import * as cp from "child_process";

export interface AgentAction {
  name: string;
  description: string;
  template: string;
  provider?: string;
  when?: {
    idMatch?: string;
    typeMatch?: string;
    stageMatch?: string;
    statusMatch?: string;
    fileMatch?: string;
  };
}

export interface ActionContext {
  id?: string;
  type?: string;
  stage?: string;
  status?: string;
  file_path?: string;
}

export interface ProviderState {
  available: boolean;
  path?: string;
  error?: string;
  latency_ms?: number;
}

export interface AgentStatus {
  last_checked: string;
  providers: { [name: string]: ProviderState };
}

export class ActionService {
  private static instance: ActionService;
  private _actions: AgentAction[] = [];
  private _providers: { [name: string]: ProviderState } = {};

  private _onDidChangeActions = new vscode.EventEmitter<AgentAction[]>();
  public readonly onDidChangeActions = this._onDidChangeActions.event;

  private _onDidChangeProviders = new vscode.EventEmitter<{
    [name: string]: ProviderState;
  }>();
  public readonly onDidChangeProviders = this._onDidChangeProviders.event;

  private constructor() {
    this.refresh();
    this.setupWatcher();
  }

  public static getInstance(): ActionService {
    if (!ActionService.instance) {
      ActionService.instance = new ActionService();
    }
    return ActionService.instance;
  }

  public getActions(): AgentAction[] {
    return this._actions;
  }

  public getProviders(): { [name: string]: ProviderState } {
    return this._providers;
  }

  public async refresh() {
    try {
      const rootPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
      if (!rootPath) {
        return;
      }

      const cmd = "monoco agent list --json";

      cp.exec(cmd, { cwd: rootPath }, (err, stdout, _stderr) => {
        if (err) {
          console.error("Failed to list actions:", err);
          return;
        }
        try {
          const actions = JSON.parse(stdout);
          this._actions = actions;
          this._onDidChangeActions.fire(this._actions);
        } catch (e) {
          console.error("Failed to parse monoco agent list output", e);
        }
      });

      this.refreshStatus();
    } catch (e) {
      console.error("Error refreshing actions", e);
    }
  }

  public async getAvailableActions(
    context: ActionContext
  ): Promise<AgentAction[]> {
    return new Promise((resolve) => {
      const rootPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
      if (!rootPath) {
        return resolve([]);
      }

      const contextJson = JSON.stringify(context);
      const cmd = `monoco agent list --json --context '${contextJson}'`;

      cp.exec(cmd, { cwd: rootPath }, (err, stdout, _stderr) => {
        if (err) {
          console.error("Failed to filter actions:", err);
          return resolve([]);
        }
        try {
          const actions = JSON.parse(stdout);
          resolve(actions);
        } catch (e) {
          console.error("Failed to parse filtered actions", e);
          resolve([]);
        }
      });
    });
  }

  public async refreshStatus() {
    try {
      const rootPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
      if (!rootPath) {
        return;
      }

      const cmd = "monoco agent status --json";
      cp.exec(cmd, { cwd: rootPath }, (err, stdout, _stderr) => {
        if (err) {
          console.error("Failed to get agent status:", err);
          return;
        }
        try {
          const status: AgentStatus = JSON.parse(stdout);
          this._providers = status.providers;
          this._onDidChangeProviders.fire(this._providers);
        } catch (e) {
          console.error("Failed to parse monoco agent status output", e);
        }
      });
    } catch (e) {
      console.error("Error refreshing status", e);
    }
  }

  private setupWatcher() {
    // Watch for .prompty files in ~/.monoco/actions and project .monoco/actions
    // For simplicity, we just watch all .prompty in workspace and a general check
    const watcher = vscode.workspace.createFileSystemWatcher(
      "**/.monoco/actions/*.prompty"
    );
    watcher.onDidChange(() => this.refresh());
    watcher.onDidCreate(() => this.refresh());
    watcher.onDidDelete(() => this.refresh());
  }

  public runAction(
    actionName: string,
    targetFile?: string,
    instruction?: string
  ) {
    const terminal = vscode.window.createTerminal(`Agent: ${actionName}`);
    terminal.show();

    let cmd = `monoco agent run ${actionName}`;
    if (targetFile) {
      cmd += ` "${targetFile}"`;
    }
    if (instruction) {
      cmd += ` --instruction "${instruction}"`;
    }

    terminal.sendText(cmd);
  }
}
