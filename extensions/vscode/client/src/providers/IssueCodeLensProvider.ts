import * as vscode from "vscode";
import { ActionService } from "../services/ActionService";

export class IssueCodeLensProvider implements vscode.CodeLensProvider {
  constructor() {}

  async provideCodeLenses(
    document: vscode.TextDocument,
    _token: vscode.CancellationToken
  ): Promise<vscode.CodeLens[]> {
    const lenses: vscode.CodeLens[] = [];

    // Position: Find "## ID: Title" line
    let line = 0;
    const text = document.getText();
    const titleRegex = /^##\s+[A-Z]+-\d+:/m;
    const match = titleRegex.exec(text);
    if (match) {
      line = document.positionAt(match.index).line;
    }
    // Alternatively fallback to status line?
    // Just use line 0 if not found, or title line.

    const range = new vscode.Range(line, 0, line, 100);

    try {
      const actions = await ActionService.getInstance().getIssueActions(
        document.uri.fsPath
      );

      for (const action of actions) {
        let command: vscode.Command;

        // Check if it's an Agent Task (has 'task' field from our backend update)
        // Or if command starts with 'monoco agent run' ?
        // Backend core.py: IssueAction(..., command="monoco agent run develop", task="develop")

        if (action.task) {
          command = {
            title: `${action.icon || ""} ${action.label}`,
            command: "monoco.runAction",
            arguments: [action.task, document.uri.fsPath],
          };
        } else if (action.command) {
          command = {
            title: `${action.icon || ""} ${action.label}`,
            command: "monoco.runTerminalCommand",
            arguments: [action.command],
          };
        } else {
          continue;
        }

        lenses.push(new vscode.CodeLens(range, command));
      }
    } catch (e) {
      // console.error("Failed to provide lenses", e);
    }

    return lenses;
  }
}
