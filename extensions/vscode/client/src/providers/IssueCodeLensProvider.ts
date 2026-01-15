import * as vscode from "vscode";

export class IssueCodeLensProvider implements vscode.CodeLensProvider {
  constructor() {}

  provideCodeLenses(
    document: vscode.TextDocument,
    _token: vscode.CancellationToken
  ): vscode.ProviderResult<vscode.CodeLens[]> {
    const lenses: vscode.CodeLens[] = [];
    const regex = /^stage:\s*(\w+)/gm;
    const text = document.getText();
    let match;

    while ((match = regex.exec(text)) !== null) {
      const line = document.positionAt(match.index).line;
      const range = new vscode.Range(line, 0, line, match[0].length);

      const cmd: vscode.Command = {
        title: "$(sparkle) Agent Actions",
        command: "monoco.showAgentActions",
        arguments: [document.uri.fsPath],
      };

      lenses.push(new vscode.CodeLens(range, cmd));
    }
    return lenses;
  }
}
