/**
 * Command Registry
 * Coordinates all command registrations
 */

import * as vscode from "vscode";
import { IssueCommands } from "./IssueCommands";
import { ActionCommands } from "./ActionCommands";
import { SettingsCommands } from "./SettingsCommands";
import { TreeViewCommands } from "./TreeViewCommands";
import { KanbanProvider } from "../webview/KanbanProvider";
import { ActionService } from "../services/ActionService";
import { AgentStateService } from "../services/AgentStateService";
import { IssueFieldControlProvider } from "../providers/IssueFieldControlProvider";
import { IssueTreeProvider } from "../views/IssueTreeProvider";
import { LanguageClientManager } from "../lsp/LanguageClientManager";

export class CommandRegistry {
  private issueCommands: IssueCommands;
  private actionCommands: ActionCommands;
  private settingsCommands: SettingsCommands;
  private treeViewCommands?: TreeViewCommands;

  constructor(
    context: vscode.ExtensionContext,
    dependencies: {
      kanbanProvider: KanbanProvider;
      actionService: ActionService;
      agentStateService: AgentStateService;
      issueFieldControl: IssueFieldControlProvider;
      runMonoco: (args: string[], cwd?: string) => Promise<string>;
      checkDependencies: () => Promise<void>;
      treeProvider?: IssueTreeProvider;
      lspManager?: LanguageClientManager;
    },
  ) {
    this.issueCommands = new IssueCommands(
      context,
      dependencies.kanbanProvider,
      dependencies.actionService,
      dependencies.issueFieldControl,
      dependencies.runMonoco,
    );

    this.actionCommands = new ActionCommands(
      context,
      dependencies.actionService,
      dependencies.agentStateService,
    );

    this.settingsCommands = new SettingsCommands(
      context,
      dependencies.checkDependencies,
      dependencies.kanbanProvider,
    );

    // Initialize TreeView commands if provider is available
    if (dependencies.treeProvider && dependencies.lspManager) {
      this.treeViewCommands = new TreeViewCommands(
        context,
        dependencies.treeProvider,
        dependencies.lspManager,
      );
    }
  }

  /**
   * Register all commands
   */
  registerAll(): void {
    this.issueCommands.registerAll();
    this.actionCommands.registerAll();
    this.settingsCommands.registerAll();
    this.treeViewCommands?.registerAll();
  }
}
