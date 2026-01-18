/**
 * Monoco Language Server
 * Provides LSP features for Monoco issue files
 */

import {
  createConnection,
  TextDocuments,
  ProposedFeatures,
  InitializeParams,
  DidChangeConfigurationNotification,
  TextDocumentSyncKind,
  InitializeResult,
  WorkspaceFolder,
  DidChangeWatchedFilesParams,
} from "vscode-languageserver/node";
import { TextDocument } from "vscode-languageserver-textdocument";
import { fileURLToPath } from "url";
import * as fs from "fs";
import * as path from "path";

// Services
import { CLIExecutor, MonocoSettings } from "./services/CLIExecutor";
import { WorkspaceIndexer } from "./services/WorkspaceIndexer";

// Providers
import { DefinitionProvider } from "./providers/DefinitionProvider";
import { CompletionProvider } from "./providers/CompletionProvider";
import { DocumentLinkProvider } from "./providers/DocumentLinkProvider";
import { DiagnosticProvider } from "./providers/DiagnosticProvider";

// Create connection
const connection = createConnection(ProposedFeatures.all);
const documents: TextDocuments<TextDocument> = new TextDocuments(TextDocument);

// State
let workspaceRoot: string | null = null;
let hasConfigurationCapability = false;
let hasWorkspaceFolderCapability = false;

// Settings
const defaultSettings: MonocoSettings = {
  executablePath: "monoco",
  webUrl: "http://127.0.0.1:8642",
};
let globalSettings: MonocoSettings = defaultSettings;

// Services
let cliExecutor: CLIExecutor;
let workspaceIndexer: WorkspaceIndexer;

// Providers
let definitionProvider: DefinitionProvider;
let completionProvider: CompletionProvider;
let documentLinkProvider: DocumentLinkProvider;
let diagnosticProvider: DiagnosticProvider;

// Initial scan promise
let initialScanResolver: () => void;
const initialScanPromise = new Promise<void>((resolve) => {
  initialScanResolver = resolve;
});

/**
 * Initialize the server
 */
connection.onInitialize((params: InitializeParams) => {
  const capabilities = params.capabilities;
  hasConfigurationCapability = !!(
    capabilities.workspace && !!capabilities.workspace.configuration
  );
  hasWorkspaceFolderCapability = !!(
    capabilities.workspace && !!capabilities.workspace.workspaceFolders
  );

  const result: InitializeResult = {
    capabilities: {
      textDocumentSync: TextDocumentSyncKind.Incremental,
      completionProvider: { resolveProvider: true },
      definitionProvider: true,
      documentLinkProvider: { resolveProvider: false },
    },
  };

  if (hasWorkspaceFolderCapability) {
    result.capabilities.workspace = {
      workspaceFolders: { supported: true },
    };
  }

  return result;
});

/**
 * Server initialized
 */
connection.onInitialized(async () => {
  if (hasConfigurationCapability) {
    connection.client.register(
      DidChangeConfigurationNotification.type,
      undefined,
    );
  }

  if (hasWorkspaceFolderCapability) {
    connection.workspace.onDidChangeWorkspaceFolders((_event: any) => {
      connection.console.log("Workspace folder change event received.");
    });
  }

  // Get workspace root and initialize services
  const folders = await connection.workspace.getWorkspaceFolders();
  if (folders && folders.length > 0) {
    workspaceRoot = fileURLToPath(folders[0].uri);

    // Initialize services
    cliExecutor = new CLIExecutor(globalSettings, (msg) =>
      connection.console.log(msg),
    );

    workspaceIndexer = new WorkspaceIndexer(workspaceRoot, cliExecutor, (msg) =>
      connection.console.log(msg),
    );

    // Initialize providers
    definitionProvider = new DefinitionProvider(
      workspaceRoot,
      cliExecutor,
      (msg) => connection.console.log(msg),
    );

    completionProvider = new CompletionProvider(workspaceIndexer);

    documentLinkProvider = new DocumentLinkProvider(workspaceIndexer);

    diagnosticProvider = new DiagnosticProvider(
      workspaceRoot,
      cliExecutor,
      (msg) => connection.console.log(msg),
    );

    // Initial scan
    await workspaceIndexer.scan();
  }

  initialScanResolver();
});

/**
 * Configuration changed
 */
connection.onDidChangeConfiguration(async (change) => {
  if (hasConfigurationCapability) {
    // Fetch new settings from client
    try {
      const config = await connection.workspace.getConfiguration("monoco");
      if (config) {
        globalSettings = {
          executablePath:
            config.executablePath || defaultSettings.executablePath,
          webUrl: config.webUrl || defaultSettings.webUrl,
        };
        cliExecutor?.updateSettings(globalSettings);
      }
    } catch (e) {
      connection.console.warn(`Failed to get configuration: ${e}`);
    }
  } else {
    globalSettings = <MonocoSettings>(
      (change.settings.monoco || defaultSettings)
    );
    cliExecutor?.updateSettings(globalSettings);
  }
});

/**
 * Document events
 */
documents.onDidOpen(async (change) => {
  await initialScanPromise;
  if (diagnosticProvider) {
    const diagnostics = await diagnosticProvider.validate(change.document);
    connection.sendDiagnostics({ uri: change.document.uri, diagnostics });
  }
});

documents.onDidSave(async (change) => {
  await initialScanPromise;
  if (diagnosticProvider) {
    const diagnostics = await diagnosticProvider.validate(change.document);
    connection.sendDiagnostics({ uri: change.document.uri, diagnostics });
  }
});

/**
 * File watcher
 */
connection.onDidChangeWatchedFiles((_change: DidChangeWatchedFilesParams) => {
  if (_change.changes.some((c) => c.uri.endsWith(".md"))) {
    workspaceIndexer?.scan();
  }
});

/**
 * Completion
 */
connection.onCompletion(async (params) => {
  await initialScanPromise;
  return completionProvider?.provideCompletion(params) ?? [];
});

connection.onCompletionResolve(async (item) => {
  await initialScanPromise;
  return completionProvider?.resolveCompletion(item) ?? item;
});

/**
 * Definition
 */
connection.onDefinition(async (params) => {
  await initialScanPromise;
  return definitionProvider?.provideDefinition(params) ?? null;
});

/**
 * Document Links
 */
connection.onDocumentLinks(async (params) => {
  await initialScanPromise;
  const document = documents.get(params.textDocument.uri);
  if (!document || !documentLinkProvider) {
    return [];
  }
  return documentLinkProvider.provideDocumentLinks(params, document);
});

/**
 * CodeLens
 */

/**
 * Custom requests for Cockpit
 */

// Get all issues
connection.onRequest("monoco/getAllIssues", async () => {
  await initialScanPromise;
  if (!workspaceIndexer) {
    connection.console.warn("[Monoco LSP] WorkspaceIndexer not initialized");
    return [];
  }
  const issues = workspaceIndexer.getAllIssues();
  connection.console.log(
    `[Monoco LSP] Serving ${issues.length} issues to Cockpit. Sample ID: ${issues[0]?.id}, Project: ${issues[0]?.project_id}`,
  );
  return issues;
});

// Get metadata (projects and last active project)
connection.onRequest("monoco/getMetadata", async () => {
  await initialScanPromise;

  if (!workspaceIndexer) {
    connection.console.warn("[Monoco LSP] WorkspaceIndexer not initialized");
    return {
      last_active_project_id: null,
      projects: [],
    };
  }

  let lastActive = null;
  if (workspaceRoot) {
    try {
      const statePath = path.join(workspaceRoot, ".monoco", "state.json");
      if (fs.existsSync(statePath)) {
        const state = JSON.parse(fs.readFileSync(statePath, "utf-8"));
        lastActive = state.last_active_project_id;
      }
    } catch (e) {
      // Ignore
    }
  }

  return {
    last_active_project_id: lastActive,
    projects: workspaceIndexer.getProjects(),
  };
});

// Update issue
connection.onRequest(
  "monoco/updateIssue",
  async (params: { id: string; changes: any }) => {
    if (!workspaceRoot) {
      return { success: false, error: "No workspace" };
    }

    const map: Record<string, string> = {
      dependencies: "--dependency",
      related: "--related",
      tags: "--tag",
    };

    const finalArgs = ["issue", "update", params.id];
    for (const [key, value] of Object.entries(params.changes)) {
      if (value === null || value === undefined) {
        continue;
      }
      if (map[key]) {
        if (Array.isArray(value)) {
          value.forEach((v: any) => finalArgs.push(map[key], String(v)));
        }
      } else {
        finalArgs.push(`--${key}`, String(value));
      }
    }

    try {
      await cliExecutor.execute(finalArgs, workspaceRoot);
      workspaceIndexer.scan(); // Refresh cache
      return { success: true };
    } catch (e: any) {
      return { success: false, error: e.message };
    }
  },
);

// Get execution profiles
connection.onRequest(
  "monoco/getExecutionProfiles",
  async (_params: { projectId: string }) => {
    if (!workspaceRoot) {
      return [];
    }
    try {
      const stdout = await cliExecutor.execute(
        ["agent", "list", "--json"],
        workspaceRoot,
      );
      return JSON.parse(stdout);
    } catch (e) {
      return [];
    }
  },
);

/**
 * Start listening
 */
/**
 * Start listening
 */
documents.listen(connection);
connection.listen();
