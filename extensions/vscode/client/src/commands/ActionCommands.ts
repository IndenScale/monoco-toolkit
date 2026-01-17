/**
 * Action Commands
 * Commands related to agent actions
 */

import * as vscode from "vscode";
import { BaseCommandRegistry } from "./BaseCommandRegistry";
import { COMMAND_IDS } from "../../../shared/constants";
import { ActionService } from "../services/ActionService";
import { AgentStateService } from "../services/AgentStateService";
import { ActionTreeItem } from "../views/ActionsTreeProvider";
import { parseFrontmatter } from "../utils/frontmatter";

export class ActionCommands extends BaseCommandRegistry {
  constructor(
    context: vscode.ExtensionContext,
    private actionService: ActionService,
    private agentStateService: AgentStateService,
  ) {
    super(context);
  }

  registerAll(): void {
    this.register(COMMAND_IDS.RUN_ACTION, async (arg1?: any, arg2?: any) => {
      let actionName: string | undefined;
      let targetFile: string | undefined;

      if (arg1 instanceof ActionTreeItem) {
        // Called from Tree View context menu
        actionName = arg1.action.name;
        targetFile = vscode.window.activeTextEditor?.document.uri.fsPath;
      } else if (typeof arg1 === "string") {
        // Called from Hover link or command palette with args
        actionName = arg1;
        targetFile = arg2;
      }

      if (!actionName) {
        const items = this.actionService.getActions().map((e) => ({
          label: e.name,
          description: e.description,
          detail: e.provider,
        }));
        const selected = await vscode.window.showQuickPick(items, {
          placeHolder: "Select Action to Run",
        });
        if (selected) {
          actionName = selected.label;
        }
      }

      if (actionName) {
        if (!targetFile) {
          targetFile = vscode.window.activeTextEditor?.document.uri.fsPath;
        }
        const instruction = await vscode.window.showInputBox({
          prompt: `Additional instruction for ${actionName} (Optional)`,
          placeHolder: "e.g. 'Focus on accuracy'",
        });

        this.actionService.runAction(actionName, targetFile, instruction);
      }
    });

    this.register(COMMAND_IDS.SHOW_AGENT_ACTIONS, async (filePath: string) => {
      const editor = vscode.window.activeTextEditor;
      let actions: any[] = [];

      if (editor && editor.document.uri.fsPath === filePath) {
        const meta = parseFrontmatter(editor.document.getText());
        actions = await this.actionService.getAvailableActions({
          id: meta.id,
          type: meta.type,
          stage: meta.stage,
          status: meta.status,
          file_path: filePath,
        });
      } else {
        actions = this.actionService.getActions();
      }

      const items = actions.map((e) => ({
        label: `$(play) ${e.name}`,
        description: e.description,
        actionName: e.name,
      }));

      const selected = await vscode.window.showQuickPick(items, {
        placeHolder: "Select Agent Action",
      });

      if (selected) {
        const instruction = await vscode.window.showInputBox({
          prompt: `Instruction for ${selected.actionName}`,
          placeHolder: "Context or specific request...",
        });
        this.actionService.runAction(
          selected.actionName,
          filePath,
          instruction,
        );
      }
    });

    this.register(COMMAND_IDS.VIEW_ACTION_TEMPLATE, async (action: any) => {
      const uri = vscode.Uri.parse(`monoco-action:${action.name}.md`);
      const doc = await vscode.workspace.openTextDocument(uri);
      await vscode.window.showTextDocument(doc, { preview: true });
    });

    this.register(COMMAND_IDS.REFRESH_PROVIDERS, () => {
      this.agentStateService.refresh();
      this.actionService.refresh();
      vscode.window.showInformationMessage("Agent status refreshed");
    });
  }
}
