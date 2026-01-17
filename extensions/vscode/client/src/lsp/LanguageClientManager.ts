/**
 * Language Server Protocol Client Manager
 * Manages the lifecycle and communication with the LSP server
 */

import * as path from "path";
import * as fs from "fs";
import * as vscode from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from "vscode-languageclient/node";

export class LanguageClientManager {
  private client?: LanguageClient;

  constructor(
    private context: vscode.ExtensionContext,
    private outputChannel: vscode.OutputChannel
  ) {}

  /**
   * Start the language server
   */
  async start(): Promise<void> {
    const serverModule = this.context.asAbsolutePath(
      path.join("server", "out", "server.js")
    );

    // Check if server module exists
    if (!fs.existsSync(serverModule)) {
      throw new Error(`LSP server module not found at: ${serverModule}`);
    }

    const serverOptions = this.createServerOptions(serverModule);
    const clientOptions = this.createClientOptions();

    this.client = new LanguageClient(
      "monocoLanguageServer",
      "Monoco Language Server",
      serverOptions,
      clientOptions
    );

    this.outputChannel.appendLine("Starting Monoco Language Server...");
    await this.client.start();
    this.outputChannel.appendLine(
      "Monoco Language Server started successfully"
    );
  }

  /**
   * Stop the language server
   */
  async stop(): Promise<void> {
    if (!this.client) {
      return;
    }

    this.outputChannel.appendLine("Stopping Monoco Language Server...");
    await this.client.stop();
    this.outputChannel.appendLine("Monoco Language Server stopped");
  }

  /**
   * Send a request to the language server
   */
  async sendRequest<T>(method: string, params?: any): Promise<T> {
    if (!this.client) {
      throw new Error("LSP client not started");
    }
    return this.client.sendRequest(method, params);
  }

  /**
   * Get the underlying language client
   */
  getClient(): LanguageClient | undefined {
    return this.client;
  }

  /**
   * Create server options with bundled binary support
   */
  private createServerOptions(serverModule: string): ServerOptions {
    // Check for bundled binary
    const bundledPath = this.getBundledBinaryPath();
    const env = { ...process.env };

    if (bundledPath && fs.existsSync(bundledPath)) {
      env["MONOCO_BUNDLED_PATH"] = bundledPath;
      this.outputChannel.appendLine(`Using bundled binary: ${bundledPath}`);
    }

    return {
      run: {
        module: serverModule,
        transport: TransportKind.ipc,
        options: { env },
      },
      debug: {
        module: serverModule,
        transport: TransportKind.ipc,
        options: {
          env,
          execArgv: ["--nolazy", "--inspect=6009"],
        },
      },
    };
  }

  /**
   * Create client options
   */
  private createClientOptions(): LanguageClientOptions {
    return {
      documentSelector: [{ scheme: "file", language: "markdown" }],
      synchronize: {
        fileEvents: vscode.workspace.createFileSystemWatcher("**/.clientrc"),
      },
    };
  }

  /**
   * Get bundled binary path
   */
  private getBundledBinaryPath(): string {
    const isWindows = process.platform === "win32";
    const binaryName = isWindows ? "monoco.exe" : "monoco";
    return this.context.asAbsolutePath(path.join("bin", binaryName));
  }
}
