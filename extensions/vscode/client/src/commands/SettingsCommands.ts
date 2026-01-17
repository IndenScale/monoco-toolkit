/**
 * Settings Commands
 * Commands related to settings and utilities
 */

import * as vscode from "vscode";
import { BaseCommandRegistry } from "./BaseCommandRegistry";
import { COMMAND_IDS } from "../../../shared/constants";
import { KanbanProvider } from "../webview/KanbanProvider";

export class SettingsCommands extends BaseCommandRegistry {
  constructor(
    context: vscode.ExtensionContext,
    private checkDependencies: () => Promise<void>,
    private kanbanProvider?: KanbanProvider,
  ) {
    super(context);
  }

  registerAll(): void {
    this.register(COMMAND_IDS.OPEN_SETTINGS, () => {
      if (this.kanbanProvider) {
        this.kanbanProvider.showSettings();
      } else {
        vscode.commands.executeCommand(
          "workbench.action.openSettings",
          "@ext:indenscale.monoco-vscode",
        );
      }
    });

    this.register(COMMAND_IDS.OPEN_WEB_UI, () => {
      const config = vscode.workspace.getConfiguration("monoco");
      const webUrl = config.get("webUrl") as string;
      if (webUrl) {
        vscode.env.openExternal(vscode.Uri.parse(webUrl));
      }
    });

    this.register(COMMAND_IDS.RUN_TERMINAL_COMMAND, (command: string) => {
      if (!command) {
        return;
      }
      const terminal =
        vscode.window.activeTerminal || vscode.window.createTerminal("Monoco");
      terminal.show();
      terminal.sendText(command);
    });

    this.register(COMMAND_IDS.CHECK_DEPENDENCIES, async () => {
      await this.checkDependencies();
    });
  }
}
