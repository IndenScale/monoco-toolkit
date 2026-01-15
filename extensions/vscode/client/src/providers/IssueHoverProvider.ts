import * as vscode from "vscode";
import { ActionService, ActionContext } from "../services/ActionService";
import { parseFrontmatter } from "../utils/frontmatter";

export class IssueHoverProvider implements vscode.HoverProvider {
  constructor(private actionService: ActionService) {}

  async provideHover(
    document: vscode.TextDocument,
    position: vscode.Position,
    _token: vscode.CancellationToken
  ): Promise<vscode.Hover | undefined> {
    const range = document.getWordRangeAtPosition(position, /^stage:\s*(\w+)/);
    if (!range) {
      return undefined;
    }

    const line = document.lineAt(position.line).text;
    const match = line.match(/^stage:\s*(\w+)/);
    if (!match) {
      return undefined;
    }

    const stageValue = match[1];

    // 1. Extract context from document
    const content = document.getText();
    const meta = parseFrontmatter(content);

    const context: ActionContext = {
      id: meta.id,
      type: meta.type,
      stage: meta.stage || stageValue,
      status: meta.status,
      file_path: document.uri.fsPath,
    };

    // 2. Fetch context-aware actions
    const actions = await this.actionService.getAvailableActions(context);
    if (actions.length === 0) {
      return undefined;
    }

    const markdown = new vscode.MarkdownString();
    markdown.isTrusted = true;
    markdown.appendMarkdown(`**Agent Actions for stage: ${stageValue}**\n\n`);

    actions.forEach((action) => {
      const args = [action.name, document.uri.fsPath];
      const commandUri = vscode.Uri.parse(
        `command:monoco.runAction?${encodeURIComponent(JSON.stringify(args))}`
      );
      markdown.appendMarkdown(
        `- [$(play) ${action.name}](${commandUri}) - ${action.description}\n`
      );
    });

    return new vscode.Hover(markdown, range);
  }
}
