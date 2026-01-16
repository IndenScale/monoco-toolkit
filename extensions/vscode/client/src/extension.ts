import * as path from "path";
import * as fs from "fs";
import * as vscode from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from "vscode-languageclient/node";

import { checkAndBootstrap } from "./bootstrap";
import { AgentStateService } from "./services/AgentStateService";
import { ActionService } from "./services/ActionService";
import { bootstrapActions } from "./services/ActionBootstrap";
import {
  ActionsTreeProvider,
  ActionTreeItem,
} from "./views/ActionsTreeProvider";
import { IssueHoverProvider } from "./providers/IssueHoverProvider";
import { IssueCodeLensProvider } from "./providers/IssueCodeLensProvider";
import { IssueFieldControlProvider } from "./providers/IssueFieldControlProvider";

let client: LanguageClient;

export async function activate(context: vscode.ExtensionContext) {
  console.log('Congratulations, your extension "monoco-vscode" is now active!');

  // Initialize Agent State Service
  new AgentStateService(context);

  // Bootstrap default actions
  await bootstrapActions();

  // 1. Start Language Server
  // The server is implemented in node
  const serverModule = context.asAbsolutePath(
    path.join("server", "out", "server.js")
  );

  // If the extension is launched in debug mode then the debug server options are used
  // Otherwise the run options are used
  const serverOptions: ServerOptions = {
    run: { module: serverModule, transport: TransportKind.ipc },
    debug: {
      module: serverModule,
      transport: TransportKind.ipc,
    },
  };

  // Options to control the language client
  const clientOptions: LanguageClientOptions = {
    // Register the server for plain text documents
    documentSelector: [{ scheme: "file", language: "markdown" }],
    synchronize: {
      // Notify the server about file changes to '.clientrc files contained in the workspace
      fileEvents: vscode.workspace.createFileSystemWatcher("**/.clientrc"),
    },
  };

  // Create the language client and start the client.
  client = new LanguageClient(
    "monocoLanguageServer",
    "Monoco Language Server",
    serverOptions,
    clientOptions
  );

  // Start the client. This will also launch the server
  client.start();

  // 2. Start Monoco Kanban (Legacy Features)
  const kanbanProvider = new MonocoKanbanProvider(context.extensionUri);

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      MonocoKanbanProvider.viewType,
      kanbanProvider
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("monoco.openKanban", () => {
      vscode.commands.executeCommand("monoco-kanban.focus");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("monoco.refreshEntry", () => {
      kanbanProvider.refresh();
      actionService.refresh();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("monoco.createIssue", () => {
      kanbanProvider.showCreateView();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("monoco.openSettings", () => {
      vscode.commands.executeCommand(
        "workbench.action.openSettings",
        "@ext:indenscale.monoco-vscode"
      );
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("monoco.openWebUI", () => {
      const config = vscode.workspace.getConfiguration("monoco");
      const webUrl = config.get("webUrl") as string;
      if (webUrl) {
        vscode.env.openExternal(vscode.Uri.parse(webUrl));
      }
    })
  );

  // Check dependencies and bootstrap if needed
  checkAndBootstrap();

  // Try to start daemon on activation
  // Daemon Auto-start removed for Pure LSP Architecture
  // 3. Start Action UI Services
  const actionService = ActionService.getInstance();

  // Register Tree View
  const actionsProvider = new ActionsTreeProvider(actionService);
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("monoco-executions", actionsProvider)
  );

  // Register Hover Provider
  context.subscriptions.push(
    vscode.languages.registerHoverProvider(
      { scheme: "file", language: "markdown" },
      new IssueHoverProvider(actionService)
    )
  );

  // Register CodeLens Provider
  context.subscriptions.push(
    vscode.languages.registerCodeLensProvider(
      { scheme: "file", language: "markdown" },
      new IssueCodeLensProvider()
    )
  );

  // Register Field Control Provider (Status/Stage)
  const issueFieldControl = new IssueFieldControlProvider();
  context.subscriptions.push(
    vscode.languages.registerDocumentLinkProvider(
      { scheme: "file", language: "markdown" },
      issueFieldControl
    )
  );

  // Register Toggle Commands
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "monoco.toggleStatus",
      async (filePath: string, line: number) => {
        const doc = await vscode.workspace.openTextDocument(filePath);
        const lineText = doc.lineAt(line).text;
        const match = lineText.match(/^status:\s*(\w+)/);
        if (match) {
          const current = match[1];
          const next = issueFieldControl.getNextValue(
            current,
            issueFieldControl.getEnumList("status")
          );

          const start = lineText.indexOf(current);
          const end = start + current.length;
          const range = new vscode.Range(line, start, line, end);

          const edit = new vscode.WorkspaceEdit();
          edit.replace(doc.uri, range, next);
          if (await vscode.workspace.applyEdit(edit)) {
            await doc.save();
          }
        }
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "monoco.toggleStage",
      async (filePath: string, line: number) => {
        const doc = await vscode.workspace.openTextDocument(filePath);
        const lineText = doc.lineAt(line).text;
        const match = lineText.match(/^stage:\s*(\w+)/);
        if (match) {
          const current = match[1];
          const next = issueFieldControl.getNextValue(
            current,
            issueFieldControl.getEnumList("stage")
          );

          const start = lineText.indexOf(current);
          const end = start + current.length;
          const range = new vscode.Range(line, start, line, end);

          const edit = new vscode.WorkspaceEdit();
          edit.replace(doc.uri, range, next);
          if (await vscode.workspace.applyEdit(edit)) {
            await doc.save();
          }
        }
      }
    )
  );

  // Register Commands
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "monoco.runAction",
      async (arg1?: any, arg2?: any) => {
        let actionName: string | undefined;
        let targetFile: string | undefined;

        if (arg1 instanceof ActionTreeItem) {
          // Called from Tree View context menu
          actionName = arg1.action.name;
          // Get active editor file if available
          targetFile = vscode.window.activeTextEditor?.document.uri.fsPath;
        } else if (typeof arg1 === "string") {
          // Called from Hover link or command palette with args
          actionName = arg1;
          targetFile = arg2;
        }

        if (!actionName) {
          const items = actionService.getActions().map((e) => ({
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
          // Ask for instruction
          const instruction = await vscode.window.showInputBox({
            prompt: `Additional instruction for ${actionName} (Optional)`,
            placeHolder: "e.g. 'Focus on accuracy'",
          });

          actionService.runAction(actionName, targetFile, instruction);
        }
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "monoco.showAgentActions",
      async (filePath: string) => {
        // 1. Get current document to extract context
        const editor = vscode.window.activeTextEditor;
        let actions: any[] = [];

        if (editor && editor.document.uri.fsPath === filePath) {
          const { parseFrontmatter } = await import("./utils/frontmatter");
          const meta = parseFrontmatter(editor.document.getText());
          actions = await actionService.getAvailableActions({
            id: meta.id,
            type: meta.type,
            stage: meta.stage,
            status: meta.status,
            file_path: filePath,
          });
        } else {
          actions = actionService.getActions();
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
          actionService.runAction(selected.actionName, filePath, instruction);
        }
      }
    )
  );

  // Template Viewer
  const templateProvider = new (class
    implements vscode.TextDocumentContentProvider
  {
    provideTextDocumentContent(uri: vscode.Uri): string {
      const name = uri.path.split(".")[0];
      const action = actionService.getActions().find((e) => e.name === name);
      if (action) {
        return `---\nname: ${action.name}\ndescription: ${action.description}\nprovider: ${action.provider}\n---\n\n${action.template}`;
      }
      return "Action not found";
    }
  })();
  context.subscriptions.push(
    vscode.workspace.registerTextDocumentContentProvider(
      "monoco-action",
      templateProvider
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "monoco.viewActionTemplate",
      async (action: any) => {
        const uri = vscode.Uri.parse(`monoco-action:${action.name}.md`);
        const doc = await vscode.workspace.openTextDocument(uri);
        await vscode.window.showTextDocument(doc, { preview: true });
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("monoco.refreshProviders", () => {
      actionService.refreshStatus();
    })
  );
}

export function deactivate(): Thenable<void> | undefined {
  if (!client) {
    return undefined;
  }
  return client.stop();
}

class MonocoKanbanProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "monoco-kanban";
  private view?: vscode.WebviewView;

  constructor(private readonly extensionUri: vscode.Uri) {}

  public resolveWebviewView(webviewView: vscode.WebviewView) {
    this.view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.extensionUri],
    };

    webviewView.webview.html = this.getHtmlForWebview();

    webviewView.webview.onDidReceiveMessage(async (data: any) => {
      switch (data.type) {
        case "GET_LOCAL_DATA": {
          try {
            const issues: any[] = await client.sendRequest(
              "monoco/getAllIssues"
            );
            const metadata: any = await client.sendRequest(
              "monoco/getMetadata"
            );

            this.view?.webview.postMessage({
              type: "DATA_UPDATED",
              payload: {
                issues,
                projects: metadata.projects,
                workspaceState: {
                  last_active_project_id: metadata.last_active_project_id,
                },
              },
            });
          } catch (e) {
            console.error("LSP Request Failed", e);
          }
          break;
        }
        case "SAVE_STATE": {
          if (data.key === "last_active_project_id") {
            const wsFolder = vscode.workspace.workspaceFolders?.[0];
            if (wsFolder) {
              const statePath = path.join(
                wsFolder.uri.fsPath,
                ".monoco",
                "state.json"
              );
              try {
                let current = {};
                if (fs.existsSync(statePath)) {
                  current = JSON.parse(fs.readFileSync(statePath, "utf-8"));
                }
                const updated = {
                  ...current,
                  last_active_project_id: data.value,
                };
                fs.writeFileSync(statePath, JSON.stringify(updated, null, 2));
              } catch (e) {
                console.error("Failed to save state.json", e);
              }
            }
          }
          break;
        }
        case "UPDATE_ISSUE": {
          await client.sendRequest("monoco/updateIssue", {
            id: data.issueId,
            changes: data.changes,
          });
          // Trigger refresh or wait for file watcher?
          // Watcher should handle it.
          break;
        }
        case "CREATE_ISSUE": {
          // Generate File
          const { title, type, parent, projectId } = data.value;
          const id = `${type.toUpperCase()}-${Math.floor(
            Math.random() * 1000
          )}`; // Simple ID gen
          const filename = `${id}-${title
            .toLowerCase()
            .replace(/\s+/g, "-")}.md`;
          // Determine path: defaults to Issues/{Type}s/open/
          // We need to know where the project root is.
          // We can ask LSP for workspace root or use vscode.workspace.rootPath
          const wsFolder = vscode.workspace.workspaceFolders?.[0];
          if (wsFolder) {
            const content = `---
id: "${id}"
type: "${type}"
status: "open"
title: "${title}"
project_id: "${projectId}"
parent: "${parent || ""}"
---

# ${title}
`;
            const folder = type === "feature" ? "Features" : "Issues"; // Simple mapping
            const uri = vscode.Uri.joinPath(
              wsFolder.uri,
              "Issues",
              folder,
              "open",
              filename
            );
            try {
              await vscode.workspace.fs.writeFile(
                uri,
                new TextEncoder().encode(content)
              );
              // Refresh will happen automatically via Watcher
            } catch (e) {
              vscode.window.showErrorMessage("Failed to create file: " + e);
            }
          }
          break;
        }
        case "OPEN_ISSUE_FILE": {
          if (data.value && data.value.path) {
            try {
              const doc = await vscode.workspace.openTextDocument(
                data.value.path
              );
              await vscode.window.showTextDocument(doc, { preview: true });
            } catch (e) {
              vscode.window.showErrorMessage(
                `Could not open file: ${data.value.path}`
              );
            }
          }
          break;
        }
        case "FETCH_EXECUTION_PROFILES": {
          try {
            // Call LSP
            const profiles = await client.sendRequest(
              "monoco/getExecutionProfiles",
              { projectId: data.projectId }
            );
            this.view?.webview.postMessage({
              type: "EXECUTION_PROFILES",
              value: profiles,
            });
          } catch (e) {
            console.error("Failed to fetch profiles via LSP", e);
          }
          break;
        }
        case "OPEN_URL": {
          if (data.url) {
            vscode.env.openExternal(vscode.Uri.parse(data.url));
          }
          break;
        }
      }
    });
  }

  private getHtmlForWebview() {
    // Note: Assuming webview assets are copied to client/out/webview
    // Or we adjust path to client/src/webview if running from source (which we are not, we run from out)
    // The previous structure copied to out/webview. We must ensure build script does this.
    // However, the uri joining here uses 'out/webview'.
    // Since now client code is in 'client/out', the 'out' segment might be
    // redundant if extensionPath points to client root?
    // context.extensionUri points to the extension root (where package.json is).
    // package.json is at root.
    // So 'out' refers to 'client/out' if we adjusted the path?
    // No. extensionUri is root.
    // Assets are in client/out/webview.
    // So path should be path.join('client', 'out', 'webview') ?
    // Check main in package.json: "./client/out/extension.js"
    // So "root" is extension root.
    // Yes: path should be "client", "out", "webview".

    // Wait, let's keep it robust.
    // The 'main' file is deep inside.
    // But extensionUri is the root.

    const webviewPath = vscode.Uri.joinPath(
      this.extensionUri,
      "client",
      "out",
      "webview"
    );

    const indexUri = vscode.Uri.joinPath(webviewPath, "index.html");
    const styleUri = this.view!.webview.asWebviewUri(
      vscode.Uri.joinPath(webviewPath, "style.css")
    );
    const scriptUri = this.view!.webview.asWebviewUri(
      vscode.Uri.joinPath(webviewPath, "main.js")
    );

    const fs = require("fs");
    // Ensure file exists before reading to avoid crashing activating extension
    if (!fs.existsSync(indexUri.fsPath)) {
      console.error(`Webview index not found at ${indexUri.fsPath}`);
      return `<html><body><h1>Error: Webview not found</h1></body></html>`;
    }

    let html = fs.readFileSync(indexUri.fsPath, "utf-8");

    const config = vscode.workspace.getConfiguration("monoco");
    const apiBase = config.get("apiBaseUrl") || "http://127.0.0.1:8642/api/v1";
    const webUrl = config.get("webUrl") || "http://127.0.0.1:8642";

    const csp = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${
      this.view!.webview.cspSource
    } 'unsafe-inline'; script-src ${
      this.view!.webview.cspSource
    } 'unsafe-inline'; connect-src http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; img-src ${
      this.view!.webview.cspSource
    } https: data:;">`;

    html = html.replace("<head>", `<head>\n${csp}`);

    html = html.replace(
      "<!-- CONFIG_INJECTION -->",
      `<script>
        window.monocoConfig = {
          apiBase: "${apiBase}",
          webUrl: "${webUrl}",
          rootPath: "${
            vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || ""
          }"
        };
      </script>`
    );

    html = html.replace('href="style.css"', `href="${styleUri}"`);
    html = html.replace('src="main.js"', `src="${scriptUri}"`);

    return html;
  }

  public refresh() {
    if (this.view) {
      this.view.webview.postMessage({ type: "REFRESH" });
    }
  }

  public showCreateView() {
    if (this.view) {
      this.view.webview.postMessage({ type: "SHOW_CREATE_VIEW" });
    }
  }
}
