import * as vscode from "vscode";
import * as child_process from "child_process";

/**
 * Toggle the status field in an Issue file
 */
export async function toggleStatus(
  uri: vscode.Uri,
  lineNumber: number,
  currentStatus: string,
  nextStatus: string
): Promise<void> {
  try {
    const document = await vscode.workspace.openTextDocument(uri);
    const line = document.lineAt(lineNumber);

    // Replace the status value
    const newText = line.text.replace(
      /^status:\s*\w+/,
      `status: ${nextStatus}`
    );

    const edit = new vscode.WorkspaceEdit();
    edit.replace(uri, line.range, newText);

    await vscode.workspace.applyEdit(edit);
    await document.save();

    // Run monoco issue lint
    await runMonocoLint(uri);

    vscode.window.showInformationMessage(
      `Status changed: ${currentStatus} → ${nextStatus}`
    );
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to toggle status: ${error}`);
  }
}

/**
 * Toggle the stage field in an Issue file
 */
export async function toggleStage(
  uri: vscode.Uri,
  lineNumber: number,
  currentStage: string,
  nextStage: string
): Promise<void> {
  try {
    const document = await vscode.workspace.openTextDocument(uri);
    const line = document.lineAt(lineNumber);

    // Replace the stage value
    const newText = line.text.replace(/^stage:\s*\w+/, `stage: ${nextStage}`);

    const edit = new vscode.WorkspaceEdit();
    edit.replace(uri, line.range, newText);

    await vscode.workspace.applyEdit(edit);
    await document.save();

    // Run monoco issue lint
    await runMonocoLint(uri);

    vscode.window.showInformationMessage(
      `Stage changed: ${currentStage} → ${nextStage}`
    );
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to toggle stage: ${error}`);
  }
}

/**
 * Select a parent Epic for an Issue
 */
export async function selectParent(
  uri: vscode.Uri,
  lineNumber: number,
  currentParent: string
): Promise<void> {
  try {
    // Fetch available epics from API
    const config = vscode.workspace.getConfiguration("monoco");
    const apiBase = (config.get("apiBaseUrl") ||
      "http://localhost:8642/api/v1") as string;

    // Get current project (simplified - should match workspace state)
    const epics = await fetchEpics(apiBase);

    // Show Quick Pick
    const items = [
      { label: "(None)", description: "Remove parent", value: "" },
      ...epics.map((epic) => ({
        label: epic.id,
        description: epic.title,
        value: epic.id,
      })),
    ];

    const selected = await vscode.window.showQuickPick(items, {
      placeHolder: `Current parent: ${currentParent}`,
      title: "Select Parent Epic",
    });

    if (selected === undefined) {
      return; // User cancelled
    }

    // Update the document
    const document = await vscode.workspace.openTextDocument(uri);
    const line = document.lineAt(lineNumber);

    const newText = selected.value
      ? line.text.replace(/^parent:.*$/, `parent: ${selected.value}`)
      : line.text.replace(/^parent:.*$/, "parent:");

    const edit = new vscode.WorkspaceEdit();
    edit.replace(uri, line.range, newText);

    await vscode.workspace.applyEdit(edit);
    await document.save();

    // Run monoco issue lint
    await runMonocoLint(uri);

    vscode.window.showInformationMessage(
      `Parent changed: ${currentParent} → ${selected.value || "(none)"}`
    );
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to select parent: ${error}`);
  }
}

/**
 * Fetch epics from Monoco API
 */
async function fetchEpics(apiBase: string): Promise<any[]> {
  try {
    // Get all projects
    const projectsRes = await fetch(`${apiBase}/projects`);
    if (!projectsRes.ok) {
      throw new Error("Failed to fetch projects");
    }
    const projects = await projectsRes.json();

    // Fetch issues from all projects and filter epics
    const allEpics: any[] = [];
    for (const project of projects) {
      const issuesRes = await fetch(
        `${apiBase}/issues?project_id=${project.id}`
      );
      if (issuesRes.ok) {
        const issues = await issuesRes.json();
        const epics = issues.filter((i: any) => i.type === "epic");
        allEpics.push(...epics);
      }
    }

    return allEpics;
  } catch (error) {
    console.error("Failed to fetch epics:", error);
    return [];
  }
}

/**
 * Run monoco issue lint on a file
 */
async function runMonocoLint(uri: vscode.Uri): Promise<void> {
  return new Promise((resolve, reject) => {
    const workspaceFolder = vscode.workspace.getWorkspaceFolder(uri);
    if (!workspaceFolder) {
      reject(new Error("No workspace folder found"));
      return;
    }

    const cwd = workspaceFolder.uri.fsPath;

    // Run monoco issue lint
    child_process.exec(
      "monoco issue lint",
      { cwd },
      (error, stdout, stderr) => {
        if (error) {
          // Show error in output channel
          const outputChannel =
            vscode.window.createOutputChannel("Monoco Lint");
          outputChannel.appendLine("=== Monoco Issue Lint ===");
          outputChannel.appendLine(stdout);
          outputChannel.appendLine(stderr);
          outputChannel.show();

          vscode.window
            .showWarningMessage(
              "Lint validation failed. Check output for details.",
              "Show Output"
            )
            .then((action) => {
              if (action === "Show Output") {
                outputChannel.show();
              }
            });
        } else {
          console.log("[Monoco] Lint passed:", stdout);
        }
        resolve();
      }
    );
  });
}
