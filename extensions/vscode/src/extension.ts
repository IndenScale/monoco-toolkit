import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import { checkAndBootstrap } from "./bootstrap";
import { IssueLensProvider } from "./providers/IssueLensProvider";
import {
  toggleStatus,
  toggleStage,
  selectParent,
} from "./commands/issueCommands";

export async function activate(context: vscode.ExtensionContext) {
  console.log('Congratulations, your extension "monoco-vscode" is now active!');

  // Kanban Sidebar
  const kanbanProvider = new MonocoKanbanProvider(context.extensionUri);

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      MonocoKanbanProvider.viewType,
      kanbanProvider
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("monoco.openKanban", () => {
      // Focus the view
      vscode.commands.executeCommand("monoco-kanban.focus");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("monoco.startDaemon", () => {
      startDaemon();
    })
  );

  // Check dependencies and bootstrap if needed
  checkAndBootstrap().then(() => {
    // Try to start daemon on activation if not running
    checkDaemonAndNotify();
  });

  context.subscriptions.push(
    vscode.commands.registerCommand("monoco.refreshEntry", () => {
      kanbanProvider.refresh();
    })
  );

  // Issue CodeLens Provider
  const issueLensProvider = new IssueLensProvider();
  context.subscriptions.push(
    vscode.languages.registerCodeLensProvider(
      { language: "markdown", scheme: "file" },
      issueLensProvider
    )
  );

  // Issue Commands
  context.subscriptions.push(
    vscode.commands.registerCommand("monoco.toggleStatus", toggleStatus)
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("monoco.toggleStage", toggleStage)
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("monoco.selectParent", selectParent)
  );

  // Refresh CodeLens when document changes
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((document) => {
      if (document.languageId === "markdown") {
        issueLensProvider.refresh();
      }
    })
  );
}

async function checkDaemonAndNotify() {
  const isRunning = await checkDaemonRunning();
  if (!isRunning) {
    // Check configuration or just auto-start if valid project
    // For now, we prefer auto-start if we are in a Monoco project
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (workspaceFolder) {
      const root = findProjectRoot(workspaceFolder.uri.fsPath);
      if (root) {
        console.log(`[Monoco] Auto-starting daemon in ${root}`);
        startDaemon(root);
        return;
      }
    }

    const result = await vscode.window.showInformationMessage(
      "Monoco Daemon is not running. Would you like to start it?",
      "Start",
      "Cancel"
    );
    if (result === "Start") {
      startDaemon();
    }
  }
}

async function checkDaemonRunning(): Promise<boolean> {
  try {
    // We use a simple fetch to check if the daemon is alive
    // Since we don't want to add many dependencies to the extension,
    // we can use a basic http request.
    // Note: global fetch is available in VS Code 1.75+
    const response = await fetch("http://127.0.0.1:8642/health");
    return response.ok;
  } catch (e) {
    return false;
  }
}

class MonocoKanbanProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "monoco-kanban";
  private _view?: vscode.WebviewView;

  constructor(private readonly _extensionUri: vscode.Uri) {}

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken
  ) {
    this._view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri],
    };

    webviewView.webview.html = this._getHtmlForWebview();

    webviewView.webview.onDidReceiveMessage(async (data: any) => {
      switch (data.type) {
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
          } else {
            vscode.window.showWarningMessage(
              "No file path provided for issue."
            );
          }
          break;
        }
        case "INFO": {
          vscode.window.showInformationMessage(data.value);
          break;
        }
        case "CREATE_ISSUE": {
          const { type, parent, projectId } = data.value;
          const title = await vscode.window.showInputBox({
            prompt: `Create ${type} under ${projectId}`,
            placeHolder: "Issue Title",
          });

          if (title) {
            try {
              // We need to fetch from extension logic as we can't fetch from here directly easily?
              // Actually we can but we should probably tell the webview to do it or do it here.
              // Webview has the endpoint. Doing it here requires 'fetch' (Node 18+ or polyfill).
              // Since VS Code ships Node, fetch might be available.
              // But wait, the Webview main.js ALREADY has the logic to talk to API.
              // Sending 'CREATE_ISSUE' to extension is only to get USER INPUT (InputBox).
              // So we should send the Title back to Webview!

              this._view?.webview.postMessage({
                type: "CREATE_ISSUE_RESPONSE",
                value: { title, type, parent, projectId },
              });
            } catch (e) {
              vscode.window.showErrorMessage(`Failed to create issue: ${e}`);
            }
          }
          break;
        }
        case "OPEN_SETTINGS": {
          const url = await vscode.window.showInputBox({
            prompt: "Monoco API Base URL",
            value: "http://localhost:8642/api/v1",
          });
          if (url) {
            await vscode.workspace
              .getConfiguration("monoco")
              .update("apiBaseUrl", url, vscode.ConfigurationTarget.Global);
            this._view?.webview.postMessage({ type: "REFRESH" }); // Full reload might be needed to re-inject? No, just refresh logic.
            vscode.commands.executeCommand(
              "workbench.action.webview.reloadWebviewAction"
            );
          }
          break;
        }
        case "OPEN_WEBUI": {
          const config = vscode.workspace.getConfiguration("monoco");
          const webUrl = config.get("webUrl") || "http://localhost:8642";
          vscode.env.openExternal(vscode.Uri.parse(webUrl as string));
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

  private _getHtmlForWebview() {
    // Point to src/webview for dev mode. In prod this should be dist or media.
    const webviewPath = vscode.Uri.joinPath(
      this._extensionUri,
      "src",
      "webview"
    );

    const indexUri = vscode.Uri.joinPath(webviewPath, "index.html");
    const styleUri = this._view!.webview.asWebviewUri(
      vscode.Uri.joinPath(webviewPath, "style.css")
    );
    const scriptUri = this._view!.webview.asWebviewUri(
      vscode.Uri.joinPath(webviewPath, "main.js")
    );

    let html = fs.readFileSync(indexUri.fsPath, "utf-8");

    // Inject Configuration
    const config = vscode.workspace.getConfiguration("monoco");
    const apiBase = config.get("apiBaseUrl") || "http://localhost:8642/api/v1";
    const webUrl = config.get("webUrl") || "http://localhost:8642";

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

    // Inject URIs
    html = html.replace('href="style.css"', `href="${styleUri}"`);
    html = html.replace('src="main.js"', `src="${scriptUri}"`);

    return html;
  }

  public refresh() {
    if (this._view) {
      this._view.webview.postMessage({ type: "REFRESH" });
    }
  }
}

function findProjectRoot(startPath: string): string | undefined {
  let currentPath = startPath;
  while (true) {
    if (
      fs.existsSync(path.join(currentPath, "monoco.yaml")) ||
      fs.existsSync(path.join(currentPath, ".monoco"))
    ) {
      return currentPath;
    }
    const parentPath = path.dirname(currentPath);
    if (parentPath === currentPath) {
      return undefined;
    }
    currentPath = parentPath;
  }
}

function startDaemon(explicitRoot?: string) {
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  let cwd = explicitRoot;

  if (!cwd && workspaceFolder) {
    cwd =
      findProjectRoot(workspaceFolder.uri.fsPath) || workspaceFolder.uri.fsPath;
  }

  // 1. Start Backend Only
  const backendTerminalName = "Monoco Backend";
  let backendTerm = vscode.window.terminals.find(
    (t) => t.name === backendTerminalName
  );
  if (!backendTerm) {
    backendTerm = vscode.window.createTerminal({
      name: backendTerminalName,
      cwd: cwd,
      iconPath: new vscode.ThemeIcon("server"),
    });
    backendTerm.sendText("monoco serve");
  }
}
