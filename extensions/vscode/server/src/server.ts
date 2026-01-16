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
  TextDocumentChangeEvent,
  TextEdit,
  WorkspaceEdit,
} from "vscode-languageserver/node";

import { TextDocument } from "vscode-languageserver-textdocument";

import * as yaml from "js-yaml";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { WorkspaceIndexer } from "./indexer";
import { fileURLToPath } from "url";

// Create a connection for the server, using Node's IPC as a transport.
// Also include all preview / proposed LSP features.
const connection = createConnection(ProposedFeatures.all);

// Create a simple text document manager.
const documents: TextDocuments<TextDocument> = new TextDocuments(TextDocument);
const indexer = new WorkspaceIndexer();
let currentWorkspaceRoot: string | null = null;
let initialScanResolver: () => void;
const initialScanPromise = new Promise<void>((resolve) => {
  initialScanResolver = resolve;
});

let hasConfigurationCapability = false;
let hasWorkspaceFolderCapability = false;
let hasDiagnosticRelatedInformationCapability = false;

interface MonocoSettings {
  executablePath: string;
  webUrl: string;
}

const defaultSettings: MonocoSettings = {
  executablePath: "monoco",
  webUrl: "http://127.0.0.1:8642",
};

let globalSettings: MonocoSettings = defaultSettings;

// Load Schema
// We expect the schema to be in ../schema/issue_schema.json relative to 'out/server.js'
// Resolving assuming __dirname is 'out'
const SCHEMA_PATH = path.resolve(__dirname, "schema", "issue_schema.json");
let issueSchema: any = null;

try {
  if (fs.existsSync(SCHEMA_PATH)) {
    const content = fs.readFileSync(SCHEMA_PATH, "utf-8");
    issueSchema = JSON.parse(content);
    connection.console.log(`[Monoco LSP] Loaded schema from ${SCHEMA_PATH}`);
  } else {
    connection.console.warn(`[Monoco LSP] Schema not found at ${SCHEMA_PATH}`);
  }
} catch (e: any) {
  connection.console.error(
    `[Monoco LSP] Failed to reload schema: ${e.message}`
  );
}

connection.onInitialize((params: InitializeParams) => {
  const capabilities = params.capabilities;

  // Does the client support the `workspace/configuration` request?
  // If not, we fall back using global settings.
  hasConfigurationCapability = !!(
    capabilities.workspace && !!capabilities.workspace.configuration
  );
  hasWorkspaceFolderCapability = !!(
    capabilities.workspace && !!capabilities.workspace.workspaceFolders
  );
  hasDiagnosticRelatedInformationCapability = !!(
    capabilities.textDocument &&
    capabilities.textDocument.publishDiagnostics &&
    capabilities.textDocument.publishDiagnostics.relatedInformation
  );

  const result: InitializeResult = {
    capabilities: {
      textDocumentSync: TextDocumentSyncKind.Incremental,
      // Tell the client that this server supports code completion.
      completionProvider: {
        resolveProvider: true,
      },
      definitionProvider: true,
    },
  };
  if (hasWorkspaceFolderCapability) {
    result.capabilities.workspace = {
      workspaceFolders: {
        supported: true,
      },
    };
  }
  return result;
});

connection.onInitialized(() => {
  if (hasConfigurationCapability) {
    // Register for all configuration changes.
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
      connection.console.log(`[Monoco LSP] Workspace folders: ${JSON.stringify(folders)}`);
      if (folders && folders.length > 0) {
        try {
          currentWorkspaceRoot = fileURLToPath(folders[0].uri);
          connection.console.log(`[Monoco LSP] Scanning workspace root: ${currentWorkspaceRoot}`);
          indexer.setWorkspaceRoot(currentWorkspaceRoot);
          
          const executable = await resolveMonocoExecutable(currentWorkspaceRoot);
          await indexer.scan(executable);
          
          connection.console.log(
            `[Monoco LSP] Indexed ${indexer.getAll().length} issues.`
          );
        } catch (e) {
          connection.console.error(`[Monoco LSP] Failed to index: ${e}`);
        }
      } else {
        connection.console.warn("[Monoco LSP] No workspace folders found.");
      }
      initialScanResolver();
    });
});

connection.onDidChangeConfiguration((change) => {
  if (hasConfigurationCapability) {
    // Reset all cached document settings
  } else {
    globalSettings = <MonocoSettings>(
      (change.settings.monoco || defaultSettings)
    );
  }
});

// The content of a text document has changed. This event is emitted
// when the text document first opened or when its content has changed.
// documents.onDidChangeContent((change) => {
//   validateTextDocument(change.document);
// });

// Only validate on open and save, because monoco CLI reads from disk
documents.onDidOpen((change) => {
  validateTextDocument(change.document);
});

documents.onDidSave((change) => {
  validateTextDocument(change.document);
});

async function validateTextDocument(textDocument: TextDocument): Promise<void> {
  const diagnostics: Diagnostic[] = [];

  // Check if this is an issue file (has frontmatter)
  const text = textDocument.getText();
  const frontmatterRegex = /^---\n([\s\S]*?)\n---/;
  const match = frontmatterRegex.exec(text);

  if (!match) {
    // Not an issue file, skip validation
    return;
  }

  // Call monoco CLI for validation (SSOT)
  try {
    const filePath = fileURLToPath(textDocument.uri);
    const cliDiagnostics = await callMonocoCLI(filePath);
    diagnostics.push(...cliDiagnostics);
  } catch (error: any) {
    // If CLI is not available or fails, show a warning
    connection.console.warn(
      `[Monoco LSP] CLI validation failed: ${error.message}`
    );

    // Fallback: Basic YAML syntax check only
    try {
      yaml.load(match[1]);
    } catch (e: any) {
      const diagnostic: Diagnostic = {
        severity: DiagnosticSeverity.Error,
        range: {
          start: textDocument.positionAt(0),
          end: textDocument.positionAt(match[0].length),
        },
        message: `YAML Error: ${e.message}`,
        source: "Monoco LSP (Fallback)",
      };
      diagnostics.push(diagnostic);
    }
  }

  connection.sendDiagnostics({ uri: textDocument.uri, diagnostics });
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

/**
 * Call monoco CLI to get diagnostics for a file.
 * Returns LSP-compatible diagnostics.
 */
async function callMonocoCLI(filePath: string): Promise<Diagnostic[]> {
  const { spawn } = await import("child_process");

  // Determine workspace root
  // Priority: 1. Find .monoco upwards from file. 2. Current workspace root. 3. File directory.
  const projectRoot = findProjectRoot(filePath);
  const workspaceRoot = projectRoot || currentWorkspaceRoot || path.dirname(filePath);
  
  connection.console.log(`[Monoco LSP] Validating ${filePath} in root ${workspaceRoot}`);

  // Determine executable path
  const executable = await resolveMonocoExecutable(workspaceRoot);

  return new Promise((resolve, reject) => {
    // Spawn monoco CLI process
    // Explicitly pass --root to enforce strict workspace check
    const args = ["--root", workspaceRoot, "issue", "lint", "--file", filePath, "--format", "json"];
    connection.console.log(`[Monoco LSP] Running: ${executable} ${args.join(" ")}`);
    
    const proc = spawn(
      executable,
      args,
      {
        cwd: workspaceRoot,
        env: process.env,
      }
    );

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("close", (code) => {
      // monoco lint exits with code 1 if there are errors, but still outputs valid JSON
      // So we accept both 0 and 1 as valid exit codes
      if (code !== 0 && code !== 1) {
        connection.console.error(`[Monoco LSP] CLI failed with code ${code}. Stderr: ${stderr}. Stdout: ${stdout}`);
        reject(new Error(`monoco CLI exited with code ${code}: ${stderr}`));
        return;
      }

      try {
        // Parse JSON output
        const cliDiagnostics = JSON.parse(stdout);

        // Convert CLI diagnostics to LSP diagnostics
        const lspDiagnostics: Diagnostic[] = cliDiagnostics.map((d: any) => ({
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
        
        connection.console.log(`[Monoco LSP] Found ${lspDiagnostics.length} diagnostics.`);
        resolve(lspDiagnostics);
      } catch (e: any) {
        connection.console.error(`[Monoco LSP] JSON Parse Error: ${e.message}. Output was: ${stdout}`);
        reject(
          new Error(
            `Failed to parse CLI output: ${e.message}\nOutput: ${stdout}`
          )
        );
      }
    });

    proc.on("error", (err) => {
      connection.console.error(`[Monoco LSP] Spawn Error: ${err.message}`);
      reject(new Error(`Failed to spawn monoco CLI: ${err.message}`));
    });
  });
}

function findLineOfKey(yamlContent: string, key: string): number {
  const lines = yamlContent.split("\n");
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim().startsWith(`${key}:`)) {
      return i;
    }
  }
  return 0;
}

function getRangeForLine(
  document: TextDocument,
  localLineIndex: number,
  offsetLineStart: number
): any {
  // frontmatter starts at 0, usually line 1 is first content.
  // The regex match puts --- at 0.
  // So yaml content starts at line 1.
  // offsetLineStart should be 1.
  const actualLine = localLineIndex + 1;

  return {
    start: { line: actualLine, character: 0 },
    end: { line: actualLine, character: 100 },
  };
}

connection.onDidChangeWatchedFiles((_change: DidChangeWatchedFilesParams) => {
  // Monitored files have change in VSCode
  connection.console.log("We received an file change event");
  for (const change of _change.changes) {
    if (change.uri.endsWith(".md")) {
      try {
        indexer.indexFile(fileURLToPath(change.uri));
      } catch (e) {
        // ignore
      }
    }
  }
});

// This handler provides the initial list of the completion items.
connection.onCompletion(
  (_textDocumentPosition: TextDocumentPositionParams): CompletionItem[] => {
    // The pass parameter contains the position of the text document in
    // which code complete got requested. For the example we ignore this
    // info and always provide the same completion items.

    // Future: Use Schema enums.

    const issues = indexer.getAll();
    return issues.map((issue) => ({
      label: issue.id,
      kind: CompletionItemKind.Reference,
      detail: `${issue.type} - ${issue.stage}`,
      documentation: issue.title,
      data: issue.id,
    }));
  }
);

// This handler resolves additional information for the item selected in
// the completion list.
connection.onCompletionResolve((item: CompletionItem): CompletionItem => {
  // We already populate detail/doc in onCompletion
  return item;
});

connection.onDefinition((params: DefinitionParams) => {
  const document = documents.get(params.textDocument.uri);
  if (!document) return null;

  const text = document.getText();
  const offset = document.offsetAt(params.position);

  // Simple regex to find the word under cursor (Issue ID pattern roughly)
  // Looking for bounds around the offset
  const fullText = text;
  // Walk back
  let start = offset;
  while (start > 0 && /[\w-]/.test(fullText[start - 1])) {
    start--;
  }
  // Walk forward
  let end = offset;
  while (end < fullText.length && /[\w-]/.test(fullText[end])) {
    end++;
  }

  const word = fullText.substring(start, end);
  const issue = indexer.get(word);

  if (issue) {
    return Location.create(issue.uri, Range.create(0, 0, 0, 0));
  }
  return null;
});

// Monoco Custom Implementations for Cockpit
connection.onRequest("monoco/getAllIssues", async () => {
  await initialScanPromise;
  return indexer.getAll();
});

connection.onRequest("monoco/getMetadata", async () => {
  await initialScanPromise;
  return indexer.getMetadata();
});

connection.onRequest(
  "monoco/updateIssue",
  async (params: { id: string; changes: any }) => {
    const issue = indexer.get(params.id);
    if (!issue) return { success: false, error: "Issue not found" };

    const args = ["issue", "update", params.id];

    for (const [key, value] of Object.entries(params.changes)) {
      if (value === null || value === undefined) continue;

      switch (key) {
        case "title":
        case "status":
        case "stage":
        case "sprint":
        case "parent":
          args.push(`--${key}`, String(value));
          break;
        case "dependencies":
          if (Array.isArray(value)) {
            value.forEach((v: string) => args.push("--dependency", v));
          }
          break;
        case "related":
          if (Array.isArray(value)) {
            value.forEach((v: string) => args.push("--related", v));
          }
          break;
        case "tags":
          if (Array.isArray(value)) {
            value.forEach((v: string) => args.push("--tag", v));
          }
          break;
      }
    }

    try {
      const cwd = currentWorkspaceRoot || path.dirname(issue.filePath);
      await execMonocoCommand(args, cwd);
      return { success: true };
    } catch (e: any) {
      return { success: false, error: e.message };
    }
  }
);

connection.onRequest(
  "monoco/getExecutionProfiles",
  async (params: { projectId: string }) => {
    return scanExecutionProfiles(currentWorkspaceRoot);
  }
);

interface ExecutionProfile {
  name: string;
  source: "Global" | "Project";
  path: string;
  content?: string;
}

function scanExecutionProfiles(projectRoot: string | null): ExecutionProfile[] {
  const profiles: ExecutionProfile[] = [];

  // 1. Global Scope
  const globalPath = path.join(os.homedir(), ".monoco", "execution");
  profiles.push(...scanDir(globalPath, "Global"));

  // 2. Project Scope
  if (projectRoot) {
    const projectPath = path.join(projectRoot, ".monoco", "execution");
    profiles.push(...scanDir(projectPath, "Project"));
  }

  return profiles;
}

function scanDir(
  basePath: string,
  source: "Global" | "Project"
): ExecutionProfile[] {
  const profiles: ExecutionProfile[] = [];
  if (!fs.existsSync(basePath) || !fs.statSync(basePath).isDirectory()) {
    return profiles;
  }

  try {
    const items = fs.readdirSync(basePath);
    for (const item of items) {
      const itemPath = path.join(basePath, item);
      if (fs.statSync(itemPath).isDirectory()) {
        const sopPath = path.join(itemPath, "SOP.md");
        if (fs.existsSync(sopPath)) {
          profiles.push({
            name: item,
            source: source,
            path: sopPath,
          });
        }
      }
    }
  } catch (e) {
    // Ignore access errors
  }
  return profiles;
}

async function execMonocoCommand(args: string[], root: string): Promise<string> {
  const { spawn } = await import("child_process");
  
  // Determine executable path
  const executable = await resolveMonocoExecutable(root);

  return new Promise((resolve, reject) => {
    // Explicitly pass --root to enforce strict workspace check
    const finalArgs = ["--root", root, ...args];
    
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
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(`Command failed with code ${code}: ${stderr}`));
      }
    });

    proc.on("error", (err) => {
      reject(new Error(`Failed to spawn command: ${err.message}`));
    });
  });
}

// Make the text document manager listen on the connection
// for open, change and close text document events
documents.listen(connection);

// Listen on the connection
connection.listen();

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
    const home = os.homedir();
    const uvPath = path.join(home, ".local", "bin", "monoco");
    if (fs.existsSync(uvPath)) {
      executable = uvPath;
    }
  }

  const devBuildPath = path.join(
    root,
    "Toolkit",
    "dist",
    "monoco"
  );
  
  // In a real extension, we would find the extension install path.
  // For local dev, we check the dist folder.
  if (fs.existsSync(devBuildPath)) {
      executable = devBuildPath;
  }
  return executable;
}
