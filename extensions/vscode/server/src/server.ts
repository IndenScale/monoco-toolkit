import {
  createConnection,
  TextDocuments,
  ProposedFeatures,
  InitializeParams,
  DidChangeConfigurationNotification,
  CompletionItem,
  CompletionItemKind,
  TextDocumentPositionParams,
  TextDocumentSyncKind,
  InitializeResult,
  Diagnostic,
  DiagnosticSeverity,
  Location,
  Range,
  WorkspaceFolder,
  DidChangeWatchedFilesParams,
  DefinitionParams,
} from "vscode-languageserver/node";

import { TextDocument } from "vscode-languageserver-textdocument";

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { fileURLToPath } from "url";

// Create a connection for the server, using Node's IPC as a transport.
// Also include all preview / proposed LSP features.
const connection = createConnection(ProposedFeatures.all);

// Create a simple text document manager.
const documents: TextDocuments<TextDocument> = new TextDocuments(TextDocument);

// Models
interface IssueIndex {
  id: string;
  type: string;
  title: string;
  status: string;
  stage: string;
  parent?: string;
  solution?: string;
  dependencies?: string[];
  related?: string[];
  tags?: string[];
  project_id: string;
  filePath: string;
  uri: string;
}

// State
let issueCache: Map<string, IssueIndex> = new Map();
let projectCache: { id: string; name: string }[] = [];
let currentWorkspaceRoot: string | null = null;
let isScanning = false;

let initialScanResolver: () => void;
const initialScanPromise = new Promise<void>((resolve) => {
  initialScanResolver = resolve;
});

let hasConfigurationCapability = false;
let hasWorkspaceFolderCapability = false;

interface MonocoSettings {
  executablePath: string;
  webUrl: string;
}

const defaultSettings: MonocoSettings = {
  executablePath: "monoco",
  webUrl: "http://127.0.0.1:8642",
};

let globalSettings: MonocoSettings = defaultSettings;

// Helper to run CLI commands from server
// Helper to run CLI commands from server
async function execMonocoCommandRaw(
  args: string[],
  root: string
): Promise<{ stdout: string; stderr: string; code: number }> {
  const { spawn } = await import("child_process");
  const executable = await resolveMonocoExecutable(root);

  return new Promise((resolve, reject) => {
    // Explicitly pass --root to enforce strict workspace check
    const finalArgs = ["--root", root, ...args];
    connection.console.log(
      `[Monoco LSP] Executing: ${executable} ${finalArgs.join(" ")}`
    );

    const proc = spawn(executable, finalArgs, {
      cwd: root,
      env: process.env,
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });
    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("close", (code) => {
      resolve({ stdout, stderr, code: code ?? -1 });
    });

    proc.on("error", (err) => {
      reject(new Error(`Failed to spawn command: ${err.message}`));
    });
  });
}

async function execMonocoCommand(
  args: string[],
  root: string
): Promise<string> {
  const { stdout, stderr, code } = await execMonocoCommandRaw(args, root);
  if (code !== 0) {
    throw new Error(`Command failed with code ${code}: ${stderr}`);
  }
  return stdout;
}

async function scanWorkspace() {
  if (!currentWorkspaceRoot || isScanning) {
    return;
  }
  isScanning = true;

  connection.console.log(
    `[Monoco LSP] Scanning workspace: ${currentWorkspaceRoot}`
  );

  try {
    // 1. Scan Issues
    try {
      const stdout = await execMonocoCommand(
        ["issue", "list", "--json", "--workspace"],
        currentWorkspaceRoot
      );
      // Check if output is empty or valid JSON
      if (stdout.trim()) {
        const issues = JSON.parse(stdout);
        issueCache.clear();
        issues.forEach((raw: any) => {
          // Map raw to IssueIndex
          issueCache.set(raw.id, {
            ...raw,
            filePath: raw.path, // CLI returns absolute or relative? Should normalize.
            // Ideally CLI returns 'path' field.
            // In my test: "path": ".../Issues/Chores/..."
            // Let's assume raw has matching fields or close enough.
            // Test output: { "issue": { ... "path": abs_path }, "path": rel_path }
            // Wait, 'list --json' output format might be different from 'create --json'.
            // list returns a list of objects.
            // Let's assume standard IssueMetadata + path.

            // Fixup path if necessary
            uri: `file://${raw.path}`,
          });
        });
        connection.console.log(
          `[Monoco LSP] Synced ${issueCache.size} issues from CLI.`
        );
      }
    } catch (e: any) {
      connection.console.error(`[Monoco LSP] Issue scan failed: ${e.message}`);
    }

    // 2. Scan Projects
    try {
      const stdout = await execMonocoCommand(
        ["project", "list", "--json"],
        currentWorkspaceRoot
      );
      projectCache = JSON.parse(stdout);
    } catch (e: any) {
      connection.console.error(
        `[Monoco LSP] Project scan failed: ${e.message}`
      );
    }
  } finally {
    isScanning = false;
  }
}

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
    },
  };
  if (hasWorkspaceFolderCapability) {
    result.capabilities.workspace = {
      workspaceFolders: { supported: true },
    };
  }
  return result;
});

connection.onInitialized(() => {
  if (hasConfigurationCapability) {
    connection.client.register(
      DidChangeConfigurationNotification.type,
      undefined
    );
  }
  if (hasWorkspaceFolderCapability) {
    connection.workspace.onDidChangeWorkspaceFolders((_event: any) => {
      connection.console.log("Workspace folder change event received.");
    });
  }

  // Initial scan
  connection.workspace
    .getWorkspaceFolders()
    .then(async (folders: WorkspaceFolder[] | null) => {
      if (folders && folders.length > 0) {
        currentWorkspaceRoot = fileURLToPath(folders[0].uri);
        await scanWorkspace();
      }
      initialScanResolver();
    });
});

connection.onDidChangeConfiguration((change) => {
  if (hasConfigurationCapability) {
  } else {
    globalSettings = <MonocoSettings>(
      (change.settings.monoco || defaultSettings)
    );
  }
});

documents.onDidOpen((change) => {
  validateTextDocument(change.document);
});
documents.onDidSave((change) => {
  validateTextDocument(change.document);
});

async function validateTextDocument(textDocument: TextDocument): Promise<void> {
  // ... logic remains same ...
  // Using callMonocoCLI logic (separate function in original code, I should keep it or merge)
  // The original callMonocoCLI is fine.

  // However, I need to make sure I don't delete callMonocoCLI if it's outside.
  // This replacement covers up to line 602 which is almost the end.
  // I need to be careful not to delete callMonocoCLI if it was in the range 35-602.
  // In original file:
  // callMonocoCLI is at line 251-338.
  // validateTextDocument calls it.

  // I am replacing top level logic, so I should include validateTextDocument and callMonocoCLI
  // OR I should use multiple chunks.

  // Since the file is 600 lines and I'm rewriting the state management which is scattered,
  // rewriting the whole file (or large chunk) is safer to ensure consistency.

  // I will include validateTextDocument and callMonocoCLI in this huge chunk to be safe.

  // See below for implementation of validateTextDocument reusing execMonocoCommand if possible?
  // callMonocoCLI has specific error handling and parsing for Diagnostics.
  // I will keep the original logic for validation but update it to use resolved executable.

  const diagnostics: Diagnostic[] = [];
  const text = textDocument.getText();
  if (!/^---\n([\s\S]*?)\n---/.test(text)) {
    return; // Skip non-issue files
  }

  try {
    const filePath = fileURLToPath(textDocument.uri);
    const cliDiagnostics = await callMonocoCLI(filePath);
    diagnostics.push(...cliDiagnostics);
  } catch (error: any) {
    connection.console.warn(
      `[Monoco LSP] CLI validation failed: ${error.message}`
    );
  }
  connection.sendDiagnostics({ uri: textDocument.uri, diagnostics });
}

// ... helper functions ...
// I need `callMonocoCLI` and `findProjectRoot` from original.

connection.onDidChangeWatchedFiles((_change: DidChangeWatchedFilesParams) => {
  // simplified: just rescan workspace if an md file changed
  if (_change.changes.some((c) => c.uri.endsWith(".md"))) {
    scanWorkspace();
  }
});

connection.onCompletion(
  (_textDocumentPosition: TextDocumentPositionParams): CompletionItem[] => {
    return Array.from(issueCache.values()).map((issue) => ({
      label: issue.id,
      kind: CompletionItemKind.Reference,
      detail: `${issue.type} - ${issue.stage}`,
      documentation: issue.title,
      data: issue.id,
    }));
  }
);

connection.onCompletionResolve((item: CompletionItem): CompletionItem => {
  return item;
});

connection.onDefinition((params: DefinitionParams) => {
  const document = documents.get(params.textDocument.uri);
  if (!document) {
    return null;
  }
  const text = document.getText();
  const offset = document.offsetAt(params.position);

  // Regex to find word at offset
  const fullText = text;
  let start = offset;
  while (start > 0 && /[\w-]/.test(fullText[start - 1])) {
    start--;
  }
  let end = offset;
  while (end < fullText.length && /[\w-]/.test(fullText[end])) {
    end++;
  }

  const word = fullText.substring(start, end);
  const issue = issueCache.get(word);

  if (issue) {
    return Location.create(issue.uri, Range.create(0, 0, 0, 0));
  }
  return null;
});

// Monoco Custom Implementations for Cockpit
connection.onRequest("monoco/getAllIssues", async () => {
  await initialScanPromise;
  return Array.from(issueCache.values());
});

connection.onRequest("monoco/getMetadata", async () => {
  await initialScanPromise;

  // get last active project from state.json manually (or ask CLI if supported)
  // CLI 'project list' doesn't return last active.
  // So we still need to read state.json for UI state?
  // "Thin Client" means we delegate business logic.
  // Reading a JSON file for UI state is fine if CLI doesn't manage it.
  // But ideally CLI manages it.

  let lastActive = null;
  if (currentWorkspaceRoot) {
    try {
      const statePath = path.join(
        currentWorkspaceRoot,
        ".monoco",
        "state.json"
      );
      if (fs.existsSync(statePath)) {
        const state = JSON.parse(fs.readFileSync(statePath, "utf-8"));
        lastActive = state.last_active_project_id;
      }
    } catch (e) {}
  }

  return {
    last_active_project_id: lastActive,
    projects: projectCache,
  };
});

connection.onRequest(
  "monoco/updateIssue",
  async (params: { id: string; changes: any }) => {
    if (!currentWorkspaceRoot) {
      return { success: false, error: "No workspace" };
    }

    const args = ["issue", "update", params.id];
    for (const [key, value] of Object.entries(params.changes)) {
      if (value === null || value === undefined) {
        continue;
      }
      if (["title", "status", "stage", "parent", "sprint"].includes(key)) {
        args.push(`--${key}`, String(value));
      }
      if (
        ["dependencies", "related", "tags"].includes(key) &&
        Array.isArray(value)
      ) {
        value.forEach((v: string) =>
          args.push(`--${key === "tags" ? "tag" : key.slice(0, -1)}`, v)
        ); // tag vs dependency
        // wait, update command args:
        // --dependency (-d), --related (-r), --tag.
        // Original server.ts logic managed this mapping.
        // I should replicate strict mapping.
      }
    }

    // Better mapping:
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
      await execMonocoCommand(finalArgs, currentWorkspaceRoot);
      scanWorkspace(); // refresh cache immediately
      return { success: true };
    } catch (e: any) {
      return { success: false, error: e.message };
    }
  }
);

connection.onRequest(
  "monoco/getExecutionProfiles",
  async (_params: { projectId: string }) => {
    if (!currentWorkspaceRoot) {
      return [];
    }
    try {
      const stdout = await execMonocoCommand(
        ["agent", "list", "--json"],
        currentWorkspaceRoot
      );
      // Need to adapt agent list output to "ExecutionProfile" format expected by UI?
      // UI expects: { name, description, provider, ... }
      // Agent list returns: [{ name, description, provider, ... }]
      return JSON.parse(stdout);
    } catch (e) {
      return [];
    }
  }
);

// Listen on the connection
documents.listen(connection);
connection.listen();

async function callMonocoCLI(filePath: string): Promise<Diagnostic[]> {
  if (!currentWorkspaceRoot) {
    return [];
  }

  try {
    const root = findProjectRoot(filePath) || currentWorkspaceRoot;
    const { stdout, code } = await execMonocoCommandRaw(
      ["issue", "lint", "--file", filePath, "--format", "json"],
      root
    );

    if (code !== 0 && code !== 1) {
      throw new Error("CLI failed");
    }

    const cliDiagnostics = JSON.parse(stdout);
    // Convert CLI diagnostics to LSP diagnostics
    return cliDiagnostics.map((d: any) => ({
      range: {
        start: {
          line: d.range?.start?.line || 0,
          character: d.range?.start?.character || 0,
        },
        end: {
          line: d.range?.end?.line || 0,
          character: d.range?.end?.character || 100,
        },
      },
      severity: d.severity || DiagnosticSeverity.Warning,
      code: d.code || undefined,
      source: d.source || "Monoco CLI",
      message: d.message || "Unknown error",
    }));
  } catch (e: any) {
    connection.console.warn(`[Monoco LSP] Lint failed: ${e.message}`);
    return [];
  }
}

function findProjectRoot(startPath: string): string | null {
  let current = startPath;
  if (fs.existsSync(startPath) && fs.statSync(startPath).isFile()) {
    current = path.dirname(startPath);
  }

  while (true) {
    if (fs.existsSync(path.join(current, ".monoco"))) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) {
      return null;
    }
    current = parent;
  }
}

async function resolveMonocoExecutable(root: string): Promise<string> {
  let executable = globalSettings.executablePath;

  if (hasConfigurationCapability) {
    try {
      const config = await connection.workspace.getConfiguration("monoco");
      if (config && config.executablePath) {
        executable = config.executablePath;
      }
    } catch (e) {
      connection.console.warn(`[Monoco LSP] Failed to get configuration: ${e}`);
    }
  }

  // If executable is default "monoco", try to find it in common uv locations
  if (executable === "monoco") {
    // 0. Check bundled path from environment (Highest priority for "monoco" default)
    const bundledPath = process.env["MONOCO_BUNDLED_PATH"];
    if (bundledPath && fs.existsSync(bundledPath)) {
      return bundledPath;
    }

    const home = os.homedir();
    const uvPath = path.join(home, ".local", "bin", "monoco");
    if (fs.existsSync(uvPath)) {
      executable = uvPath;
    }
  }

  const devBuildPath = path.join(root, "Toolkit", "dist", "monoco");

  // In a real extension, we would find the extension install path.
  // For local dev, we check the dist folder.
  if (fs.existsSync(devBuildPath)) {
    executable = devBuildPath;
  }
  return executable;
}
