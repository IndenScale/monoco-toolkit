import * as vscode from "vscode";
import { IssueParser, FieldLocation } from "./IssueParser";

/**
 * Provides CodeLens for Issue file fields
 */
export class IssueLensProvider implements vscode.CodeLensProvider {
  private onDidChangeCodeLensesEmitter: vscode.EventEmitter<void> =
    new vscode.EventEmitter<void>();
  public readonly onDidChangeCodeLenses: vscode.Event<void> =
    this.onDidChangeCodeLensesEmitter.event;

  /**
   * Refresh CodeLens (call when file changes)
   */
  public refresh(): void {
    this.onDidChangeCodeLensesEmitter.fire();
  }

  provideCodeLenses(
    document: vscode.TextDocument
  ): vscode.CodeLens[] | Thenable<vscode.CodeLens[]> {
    // Only process valid Issue files
    if (!IssueParser.isValidIssueDocument(document)) {
      return [];
    }

    const lenses: vscode.CodeLens[] = [];
    const fieldLocations = IssueParser.findFieldLocations(document);

    fieldLocations.forEach((location) => {
      switch (location.field) {
        case "status":
          lenses.push(this.createStatusLens(document, location));
          break;
        case "stage":
          lenses.push(this.createStageLens(document, location));
          break;
        case "parent":
          lenses.push(this.createParentLens(document, location));
          break;
        // Future: dependencies, related, tags
      }
    });

    return lenses;
  }

  private createStatusLens(
    document: vscode.TextDocument,
    location: FieldLocation
  ): vscode.CodeLens {
    const currentStatus = location.value;
    const statusCycle: Record<string, string> = {
      open: "closed",
      closed: "backlog",
      backlog: "open",
    };
    const nextStatus = statusCycle[currentStatus] || "open";

    return new vscode.CodeLens(location.range, {
      title: `⚡ Toggle Status (${currentStatus} → ${nextStatus})`,
      command: "monoco.toggleStatus",
      arguments: [document.uri, location.line, currentStatus, nextStatus],
    });
  }

  private createStageLens(
    document: vscode.TextDocument,
    location: FieldLocation
  ): vscode.CodeLens {
    const currentStage = location.value;
    const stageCycle: Record<string, string> = {
      todo: "doing",
      doing: "review",
      review: "done",
      done: "todo",
    };
    const nextStage = stageCycle[currentStage] || "doing";

    return new vscode.CodeLens(location.range, {
      title: `🔄 Next Stage (${currentStage} → ${nextStage})`,
      command: "monoco.toggleStage",
      arguments: [document.uri, location.line, currentStage, nextStage],
    });
  }

  private createParentLens(
    document: vscode.TextDocument,
    location: FieldLocation
  ): vscode.CodeLens {
    const currentParent = location.value || "(none)";

    return new vscode.CodeLens(location.range, {
      title: `📎 Change Parent (${currentParent})`,
      command: "monoco.selectParent",
      arguments: [document.uri, location.line, currentParent],
    });
  }
}
