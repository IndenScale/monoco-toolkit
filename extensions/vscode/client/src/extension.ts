import * as path from "path";
import * as fs from "fs";
import * as vscode from "vscode";
import { exec } from "child_process";
import { promisify } from "util";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from "vscode-languageclient/node";

import { checkAndBootstrap, getBundledBinaryPath } from "./bootstrap";
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
import { parseFrontmatter } from "./utils/frontmatter";

async function runMonoco(args: string[], cwd?: string): Promise<string> {
  const config = vscode.workspace.getConfiguration("monoco");
  let executable = config.get<string>("executablePath") || "monoco";

  // If executable is just "monoco", we might need to rely on PATH or uv
  // For now, trust the configuration or PATH.

  // Escape args
  const escapedArgs = args.map((a) => {
    if (/^[\w\d\-_]+$/.test(a)) {
      return a;
    }
    return `"${a.replace(/"/g, '\\"')}"`;
  });

  const cmd = `${executable} ${escapedArgs.join(" ")}`;
  const workspaceRoot =
    cwd || vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

  if (!workspaceRoot) {
    throw new Error("No workspace root found");
  }

  // Use execAsync from existing promisify
  const result = await execAsync(cmd, { cwd: workspaceRoot });
  return result.stdout.trim();
}

const execAsync = promisify(exec);

let client: LanguageClient;
let outputChannel: vscode.OutputChannel;

async function checkDependencies() {
  outputChannel.appendLine("Checking dependencies...");

  try {
    // Check if uv is available
    const uvCheck = await execAsync("uv --version");
    outputChannel.appendLine(`✓ uv version: ${uvCheck.stdout.trim()}`);
  } catch (error) {
    outputChannel.appendLine("✗ uv is not available");

    // Show notification to guide user to install uv
    const installOption = "Install uv";
    const option = await vscode.window.showErrorMessage(
      "uv is not installed or not in PATH. Would you like to install it?",
      installOption
    );

    if (option === installOption) {
      // Open installation guide in browser
      await vscode.env.openExternal(
        vscode.Uri.parse(
          "https://docs.astral.sh/uv/getting-started/installation/"
        )
      );
    }
  }

  try {
    // Check if monoco is available via uv run tool by attempting to run it
    const versionResult = await execAsync(
      "uv tool run --from monoco-toolkit monoco --version"
    );
    outputChannel.appendLine(
      `✓ monoco version: ${versionResult.stdout.trim()}`
    );
  } catch (error) {
    outputChannel.appendLine("✗ monoco is not available via uv run tool");

    // Attempt to install monoco automatically
    const installOption = "Install monoco";
    const manualOption = "Manual Install";
    const option = await vscode.window.showErrorMessage(
      "monoco is not installed via uv. Would you like to install it automatically or view manual installation?",
      installOption,
      manualOption
    );

    if (option === installOption) {
      try {
        outputChannel.appendLine(
          "Installing monoco via 'uv tool install monoco-toolkit'..."
        );
        await execAsync("uv tool install monoco-toolkit --force");
        outputChannel.appendLine("✓ monoco installed successfully via uv tool");

        // Verify installation after installing
        const verifyResult = await execAsync(
          "uv tool run --from monoco-toolkit monoco --version"
        );
        outputChannel.appendLine(
          `✓ Verified monoco version: ${verifyResult.stdout.trim()}`
        );
      } catch (installError) {
        outputChannel.appendLine(`✗ Failed to install monoco: ${installError}`);
        vscode.window.showErrorMessage(
          `Failed to install monoco: ${installError}`
        );
      }
    } else if (option === manualOption) {
      // Open installation guide in browser
      await vscode.env.openExternal(
        vscode.Uri.parse("https://github.com/IndenScale/Monoco")
      );
    }
  }
}

export async function activate(context: vscode.ExtensionContext) {
  outputChannel = vscode.window.createOutputChannel("Monoco");
  outputChannel.appendLine("Monoco extension activated!");

  // Initialize Agent State Service
  new AgentStateService(context);

  // Bootstrap default actions
  await bootstrapActions();

  // Check dependencies and show diagnostics
  await checkDependencies();

  // Register command to manually check dependencies
  context.subscriptions.push(
    vscode.commands.registerCommand("monoco.checkDependencies", async () => {
      outputChannel.show(); // Show the output channel when command is run
      await checkDependencies();
    })
  );

  // 1. Start Language Server
  // The server is implemented in node
  const serverModule = context.asAbsolutePath(
    path.join("server", "out", "server.js")
  );

  // If the extension is launched in debug mode then the debug server options are used
  // Otherwise the run options are used

  // Check for bundled binary
  const bundledPath = getBundledBinaryPath(context);
  const env = { ...process.env };
  if (fs.existsSync(bundledPath)) {
    env["MONOCO_BUNDLED_PATH"] = bundledPath;
  }

  const serverOptions: ServerOptions = {
    run: {
      module: serverModule,
      transport: TransportKind.ipc,
      options: { env },
    },
    debug: {
      module: serverModule,
      transport: TransportKind.ipc,
      options: { env },
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
  checkAndBootstrap(context);

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
      async (filePath: string, _line: number) => {
        const doc = await vscode.workspace.openTextDocument(filePath);
        const text = doc.getText();
        const meta = parseFrontmatter(text);

        if (!meta.id || !meta.status) {
          vscode.window.showErrorMessage("Could not parse Issue ID or Status.");
          return;
        }

        const current = meta.status;
        const next = issueFieldControl.getNextValue(
          current,
          issueFieldControl.getEnumList("status")
        );

        try {
          await runMonoco(["issue", "update", meta.id, "--status", next]);
          // No need to manually edit file, the file watcher (LSP) will update diagnostics
          // But VS Code editor won't update automatically unless file changes on disk.
          // CLI updates the file, so VS Code should reload it automatically.
        } catch (e: any) {
          vscode.window.showErrorMessage(
            `Failed to update status: ${e.message}`
          );
        }
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "monoco.toggleStage",
      async (filePath: string, _line: number) => {
        const doc = await vscode.workspace.openTextDocument(filePath);
        const text = doc.getText();
        const meta = parseFrontmatter(text);

        if (!meta.id || !meta.stage) {
          vscode.window.showErrorMessage("Could not parse Issue ID or Stage.");
          return;
        }

        const current = meta.stage;
        const next = issueFieldControl.getNextValue(
          current,
          issueFieldControl.getEnumList("stage")
        );

        try {
          await runMonoco(["issue", "update", meta.id, "--stage", next]);
        } catch (e: any) {
          vscode.window.showErrorMessage(
            `Failed to update stage: ${e.message}`
          );
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
          const { title, type, parent } = data.value;
          const args = ["issue", "create", type, "--title", title, "--json"];
          if (parent) {
            args.push("--parent", parent);
          }

          try {
            // We use the workspace root. CLI handles Subproject resolution if configured.
            const output = await runMonoco(args);
            const result = JSON.parse(output);

            // Prefer absolute path from issue object, fallback to relative path
            let filePath = result.issue?.path || result.path;

            if (filePath) {
              const wsFolder = vscode.workspace.workspaceFolders?.[0];
              if (wsFolder) {
                const uri = path.isAbsolute(filePath)
                  ? vscode.Uri.file(filePath)
                  : vscode.Uri.joinPath(wsFolder.uri, filePath);

                const doc = await vscode.workspace.openTextDocument(uri);
                await vscode.window.showTextDocument(doc, { preview: true });
              }
            }
          } catch (e: any) {
            vscode.window.showErrorMessage(
              "Failed to create issue: " + e.message
            );
            console.error(e);
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
