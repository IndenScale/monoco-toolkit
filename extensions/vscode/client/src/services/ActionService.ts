import * as vscode from "vscode";
import * as cp from "child_process";
import { resolveMonocoExecutable } from "../bootstrap";
import { AgentTaskTerminal } from "../terminals/AgentTaskTerminal";

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

export class ActionService {
  private static instance: ActionService;
  private _actions: AgentAction[] = [];

  private _onDidChangeActions = new vscode.EventEmitter<AgentAction[]>();
  public readonly onDidChangeActions = this._onDidChangeActions.event;

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

  public async refresh() {
    try {
      const rootPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
      if (!rootPath) {
        return;
      }

      const executable = await resolveMonocoExecutable();
      const cmd = `${executable} agent list --json`;
      console.log(`[Monoco] Executing: ${cmd}`);

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
    } catch (e) {
      console.error("Error refreshing actions", e);
    }
  }

  public async getAvailableActions(
    context: ActionContext,
  ): Promise<AgentAction[]> {
    const rootPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!rootPath) {
      return [];
    }

    const executable = await resolveMonocoExecutable();
    const contextJson = JSON.stringify(context);
    const cmd = `${executable} agent list --json --context '${contextJson}'`;

    return new Promise((resolve) => {
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

  public async getIssueActions(filePath: string): Promise<any[]> {
    const rootPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!rootPath) {
      return [];
    }

    const executable = await resolveMonocoExecutable();
    const cmd = `${executable} issue inspect "${filePath}" --json`;

    return new Promise((resolve) => {
      cp.exec(cmd, { cwd: rootPath }, (err, stdout, _stderr) => {
        if (err) {
          return resolve([]);
        }
        try {
          const meta = JSON.parse(stdout);
          resolve(meta.actions || []);
        } catch (e) {
          console.error("Failed to parse monoco issue inspect output", e);
          resolve([]);
        }
      });
    });
  }

  private setupWatcher() {
    const watcher = vscode.workspace.createFileSystemWatcher(
      "**/.monoco/actions/*.prompty",
    );
    watcher.onDidChange(() => this.refresh());
    watcher.onDidCreate(() => this.refresh());
    watcher.onDidDelete(() => this.refresh());
  }

  public async runAction(
    actionName: string,
    targetFile?: string,
    instruction?: string,
  ) {
    const pty = new AgentTaskTerminal(actionName, targetFile, instruction);
    const terminal = vscode.window.createTerminal({
      name: `Agent: ${actionName}`,
      pty,
    });
    terminal.show();
  }
}
