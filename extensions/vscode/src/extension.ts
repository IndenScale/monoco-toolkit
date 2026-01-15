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
  // We run this in parallel with daemon check because bootstrap might check for global CLI
  // while we can run via 'uv run' locally even if global is missing.
  checkAndBootstrap();

  // Try to start daemon on activation
  checkDaemonAndNotify();

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
  console.log(`[Monoco] Daemon status: ${isRunning ? "Running" : "Stopped"}`);

  if (!isRunning) {
    // Check configuration or just auto-start if valid project
    // For now, we prefer auto-start if we are in a Monoco project
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (workspaceFolder) {
      const root = findProjectRoot(workspaceFolder.uri.fsPath);
      console.log(`[Monoco] Project Root check: ${root}`);

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
        case "OPEN_FILE": {
          if (data.path) {
            try {
              const doc = await vscode.workspace.openTextDocument(data.path);
              await vscode.window.showTextDocument(doc, { preview: true });
            } catch (e) {
              vscode.window.showErrorMessage(
                `Could not open file: ${data.path}`
              );
            }
          }
          break;
        }
        case "FETCH_EXECUTION_PROFILES": {
          const profiles = await scanExecutionProfiles();
          this.view?.webview.postMessage({
            type: "EXECUTION_PROFILES",
            value: profiles,
          });
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

              this.view?.webview.postMessage({
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
            value: "http://127.0.0.1:8642/api/v1",
          });
          if (url) {
            await vscode.workspace
              .getConfiguration("monoco")
              .update("apiBaseUrl", url, vscode.ConfigurationTarget.Global);
            this.view?.webview.postMessage({ type: "REFRESH" }); // Full reload might be needed to re-inject? No, just refresh logic.
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

  private getHtmlForWebview() {
    // Point to out/webview for prod mode (copied by build script).
    const webviewPath = vscode.Uri.joinPath(
      this.extensionUri,
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

    let html = fs.readFileSync(indexUri.fsPath, "utf-8");

    // Inject Configuration
    const config = vscode.workspace.getConfiguration("monoco");
    const apiBase = config.get("apiBaseUrl") || "http://127.0.0.1:8642/api/v1";
    const webUrl = config.get("webUrl") || "http://127.0.0.1:8642";

    console.log(`[Monoco] Injecting config - API: ${apiBase}, Web: ${webUrl}`);

    // CSP: Allow styles/scripts from extension, and connect to localhost API
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

    // Inject URIs
    html = html.replace('href="style.css"', `href="${styleUri}"`);
    html = html.replace('src="main.js"', `src="${scriptUri}"`);

    return html;
  }

  public refresh() {
    if (this.view) {
      this.view.webview.postMessage({ type: "REFRESH" });
    }
  }
}

async function scanExecutionProfiles(): Promise<any[]> {
  const profiles: any[] = [];
  const homedir = require("os").homedir();
  const globalPath = path.join(homedir, ".monoco", "execution");
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  const projectPath = workspaceFolder
    ? path.join(workspaceFolder, ".monoco", "execution")
    : null;

  async function scanDir(basePath: string, source: string) {
    if (fs.existsSync(basePath)) {
      const actions = fs.readdirSync(basePath);
      for (const action of actions) {
        const actionDir = path.join(basePath, action);
        if (fs.statSync(actionDir).isDirectory()) {
          const sopPath = path.join(actionDir, "SOP.md");
          if (fs.existsSync(sopPath)) {
            profiles.push({
              name: action, // e.g. "implement"
              source: source, // "Global" or "Project"
              path: sopPath,
            });
          }
        }
      }
    }
  }

  await scanDir(globalPath, "Global");
  if (projectPath) {
    await scanDir(projectPath, "Project");
  }

  return profiles;
}

function findProjectRoot(startPath: string): string | undefined {
  let currentPath = startPath;
  while (true) {
    if (fs.existsSync(path.join(currentPath, ".monoco"))) {
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
  }

  backendTerm.show();
  // Always try to start since we only call this if health check failed
  backendTerm.sendText("uv run monoco serve");
}
