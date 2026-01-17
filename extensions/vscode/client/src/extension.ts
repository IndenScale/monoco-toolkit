/**
 * Monoco VSCode Extension Entry Point
 * Refactored to use modular architecture
 */

import { exec } from "child_process";
import { promisify } from "util";

import * as vscode from "vscode";
import { checkAndBootstrap, resolveMonocoExecutable } from "./bootstrap";
import { AgentStateService } from "./services/AgentStateService";
import { ActionService } from "./services/ActionService";
import { bootstrapActions } from "./services/ActionBootstrap";

import { LanguageClientManager } from "./lsp/LanguageClientManager";
import { KanbanProvider } from "./webview/KanbanProvider";
import { ProviderRegistry } from "./providers/ProviderRegistry";
import { CommandRegistry } from "./commands/CommandRegistry";
import { VIEW_TYPES } from "../../shared/constants";

const execAsync = promisify(exec);
let outputChannel: vscode.OutputChannel;
let lspManager: LanguageClientManager;

/**
 * Execute Monoco CLI command
 */
async function runMonoco(args: string[], cwd?: string): Promise<string> {
  const executable = await resolveMonocoExecutable();

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

  const result = await execAsync(cmd, { cwd: workspaceRoot });
  return result.stdout.trim();
}

/**
 * Check dependencies (uv and monoco)
 */
async function checkDependencies(): Promise<void> {
  outputChannel.appendLine("Checking dependencies...");

  try {
    const uvCheck = await execAsync("uv --version");
    outputChannel.appendLine(`✓ uv version: ${uvCheck.stdout.trim()}`);
  } catch (error) {
    outputChannel.appendLine("✗ uv is not available");
    const installOption = "Install uv";
    const option = await vscode.window.showErrorMessage(
      "uv is not installed or not in PATH. Would you like to install it?",
      installOption,
    );

    if (option === installOption) {
      await vscode.env.openExternal(
        vscode.Uri.parse(
          "https://docs.astral.sh/uv/getting-started/installation/",
        ),
      );
    }
  }

  try {
    const executable = await resolveMonocoExecutable();
    const versionResult = await execAsync(`${executable} --version`);
    outputChannel.appendLine(
      `✓ monoco version: ${versionResult.stdout.trim()} (Source: ${executable})`,
    );
  } catch (error) {
    outputChannel.appendLine("✗ monoco is not available");
    const installOption = "Install monoco (Global)";
    const manualOption = "Manual Install";
    const option = await vscode.window.showErrorMessage(
      "monoco is not found in your environment. Would you like to install it globally via uv?",
      installOption,
      manualOption,
    );

    if (option === installOption) {
      try {
        outputChannel.appendLine(
          "Installing monoco via 'uv tool install monoco-toolkit'...",
        );
        await execAsync("uv tool install monoco-toolkit --force");
        outputChannel.appendLine("✓ monoco installed successfully via uv tool");

        const executable = await resolveMonocoExecutable();
        const verifyResult = await execAsync(`${executable} --version`);
        outputChannel.appendLine(
          `✓ Verified monoco version: ${verifyResult.stdout.trim()}`,
        );
      } catch (installError) {
        outputChannel.appendLine(`✗ Failed to install monoco: ${installError}`);
        vscode.window.showErrorMessage(
          `Failed to install monoco: ${installError}`,
        );
      }
    } else if (option === manualOption) {
      await vscode.env.openExternal(
        vscode.Uri.parse("https://github.com/IndenScale/Monoco"),
      );
    }
  }
}

/**
 * Activate extension
 */
export async function activate(context: vscode.ExtensionContext) {
  outputChannel = vscode.window.createOutputChannel("Monoco");
  outputChannel.appendLine("Monoco extension activated!");

  // 1. Initialize Agent State Service
  const agentStateService = new AgentStateService(context, runMonoco);

  // 2. Bootstrap default actions
  await bootstrapActions();

  // 4. Start LSP client
  lspManager = new LanguageClientManager(context, outputChannel);

  // 5. Initialize services
  const actionService = ActionService.getInstance();
  const kanbanProvider = new KanbanProvider(
    context.extensionUri,
    lspManager,
    runMonoco,
    agentStateService,
    outputChannel,
  );

  // Background Initialization to prevent blocking activation
  vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Window,
      title: "Initializing Monoco...",
    },
    async () => {
      try {
        await checkDependencies();
        await lspManager.start();
        // Notify webview that LSP is ready
        kanbanProvider.refresh();
      } catch (err) {
        outputChannel.appendLine(`Initialization failed: ${err}`);
      }
    },
  );

  // 6. Register providers
  const providerRegistry = new ProviderRegistry(context, actionService);
  const issueFieldControl = providerRegistry.registerAll();

  // 7. Register commands
  const commandRegistry = new CommandRegistry(context, {
    kanbanProvider,
    actionService,
    agentStateService,
    issueFieldControl,
    runMonoco,
    checkDependencies,
  });
  commandRegistry.registerAll();

  // 8. Register webview
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      VIEW_TYPES.KANBAN,
      kanbanProvider,
    ),
  );

  // 10. Register action template provider
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
      templateProvider,
    ),
  );

  // 11. Bootstrap dependencies if needed
  checkAndBootstrap(context);
}

/**
 * Deactivate extension
 */
export async function deactivate(): Promise<void> {
  if (lspManager) {
    await lspManager.stop();
  }
}
