/**
 * Command Registry
 * Coordinates all command registrations
 */

import * as vscode from "vscode";
import { IssueCommands } from "./IssueCommands";
import { ActionCommands } from "./ActionCommands";
import { SettingsCommands } from "./SettingsCommands";
import { KanbanProvider } from "../webview/KanbanProvider";
import { ActionService } from "../services/ActionService";
import { AgentStateService } from "../services/AgentStateService";
import { IssueFieldControlProvider } from "../providers/IssueFieldControlProvider";

export class CommandRegistry {
  private issueCommands: IssueCommands;
  private actionCommands: ActionCommands;
  private settingsCommands: SettingsCommands;

  constructor(
    context: vscode.ExtensionContext,
    dependencies: {
      kanbanProvider: KanbanProvider;
      actionService: ActionService;
      agentStateService: AgentStateService;
      issueFieldControl: IssueFieldControlProvider;
      runMonoco: (args: string[], cwd?: string) => Promise<string>;
      checkDependencies: () => Promise<void>;
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
  }

  /**
   * Register all commands
   */
  registerAll(): void {
    this.issueCommands.registerAll();
    this.actionCommands.registerAll();
    this.settingsCommands.registerAll();
  }
}
