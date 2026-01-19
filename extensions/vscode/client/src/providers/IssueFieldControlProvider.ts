import * as vscode from "vscode";

export class IssueFieldControlProvider implements vscode.DocumentLinkProvider {
  // Enum definitions based on schema
  private readonly statusEnum = ["open", "closed", "backlog"];
  private readonly stageEnum = ["draft", "doing", "review", "done", "freezed"];

  provideDocumentLinks(
    document: vscode.TextDocument,
    _token: vscode.CancellationToken
  ): vscode.ProviderResult<vscode.DocumentLink[]> {
    const links: vscode.DocumentLink[] = [];
    const text = document.getText();

    // Regex for Status
    // Matches "status: value"
    const statusRegex = /^status:\s*(\w+)/gm;
    let match;
    while ((match = statusRegex.exec(text)) !== null) {
      const line = document.positionAt(match.index).line;
      const value = match[1];

      // The range should cover the value itself (e.g., "open")
      // match[0] is "status: open"
      // We need the offset of the value within the match
      const valueStartOffset = match[0].indexOf(value);
      const startPos = document.positionAt(match.index + valueStartOffset);
      const endPos = document.positionAt(match.index + valueStartOffset + value.length);
      const range = new vscode.Range(startPos, endPos);

      // Create DocumentLink
      const link = new vscode.DocumentLink(range);
      link.tooltip = "Click to toggle Status";

      // Construct command URI
      const args = [document.uri.fsPath, line];
      const commandUri = vscode.Uri.parse(
        `command:monoco.toggleStatus?${encodeURIComponent(JSON.stringify(args))}`
      );
      link.target = commandUri;

      links.push(link);
    }

    // Regex for Stage
    const stageRegex = /^stage:\s*(\w+)/gm;
    while ((match = stageRegex.exec(text)) !== null) {
      const line = document.positionAt(match.index).line;
      const value = match[1];

      const valueStartOffset = match[0].indexOf(value);
      const startPos = document.positionAt(match.index + valueStartOffset);
      const endPos = document.positionAt(match.index + valueStartOffset + value.length);
      const range = new vscode.Range(startPos, endPos);

      // Create DocumentLink
      const link = new vscode.DocumentLink(range);
      link.tooltip = "Click to toggle Stage";

      const args = [document.uri.fsPath, line];
      const commandUri = vscode.Uri.parse(
        `command:monoco.toggleStage?${encodeURIComponent(JSON.stringify(args))}`
      );
      link.target = commandUri;

      links.push(link);
    }

    return links;
  }

  public getNextValue(current: string, enumList: string[]): string {
    const index = enumList.indexOf(current);
    if (index === -1) {
      return enumList[0];
    }
    return enumList[(index + 1) % enumList.length];
  }

  public getEnumList(type: "status" | "stage"): string[] {
    return type === "status" ? this.statusEnum : this.stageEnum;
  }
}
