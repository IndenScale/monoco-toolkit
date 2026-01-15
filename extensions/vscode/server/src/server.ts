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

let hasConfigurationCapability = false;
let hasWorkspaceFolderCapability = false;
let hasDiagnosticRelatedInformationCapability = false;

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
    connection.workspace.onDidChangeWorkspaceFolders(
      (_event) => {
        connection.console.log("Workspace folder change event received.");
      }
    );
  }

  // Initial scan
  connection.workspace
    .getWorkspaceFolders()
    .then((folders: WorkspaceFolder[] | null) => {
      if (folders && folders.length > 0) {
        try {
          currentWorkspaceRoot = fileURLToPath(folders[0].uri);
          indexer.setWorkspaceRoot(currentWorkspaceRoot);
          indexer.scan();
          connection.console.log(
            `[Monoco LSP] Indexed ${indexer.getAll().length} issues.`
          );
        } catch (e) {
          connection.console.error(`[Monoco LSP] Failed to index: ${e}`);
        }
      }
    });
});

// The content of a text document has changed. This event is emitted
// when the text document first opened or when its content has changed.
documents.onDidChangeContent(
  (change: TextDocumentChangeEvent<TextDocument>) => {
    validateTextDocument(change.document);
  }
);

async function validateTextDocument(textDocument: TextDocument): Promise<void> {
  const text = textDocument.getText();
  const diagnostics: Diagnostic[] = [];

  // 1. Identify Frontmatter
  // Regex to match start of file
  const frontmatterRegex = /^---\n([\s\S]*?)\n---/;
  const match = frontmatterRegex.exec(text);

  if (!match) {
    // No frontmatter, maybe not an issue file or just empty
    // We could warn if it looks like an issue ID filename but has no FM.
    return;
  }

  const frontmatterContent = match[1];
  const frontmatterEndIndex = match[0].length;
  // Use yaml parser to get object
  let data: any;
  try {
    data = yaml.load(frontmatterContent);
  } catch (e: any) {
    // YAML Syntax error
    const diagnostic: Diagnostic = {
      severity: DiagnosticSeverity.Error,
      range: {
        start: textDocument.positionAt(0),
        end: textDocument.positionAt(frontmatterEndIndex),
      },
      message: `YAML Error: ${e.message}`,
      source: "Monoco LSP",
    };
    diagnostics.push(diagnostic);
    connection.sendDiagnostics({ uri: textDocument.uri, diagnostics });
    return;
  }

  if (!data || typeof data !== "object") {
    return;
  }

  // 2. Validate against logic
  // "status: closed -> stage: done"
  if (data.status === "closed" && data.stage !== "done") {
    const stageLine = findLineOfKey(frontmatterContent, "stage");
    const range = getRangeForLine(textDocument, stageLine, 3); // Approx logic to map back to file pos

    const diagnostic: Diagnostic = {
      severity: DiagnosticSeverity.Error,
      range: range,
      message: `Invalid state: If status is 'closed', stage must be 'done'. Found: '${data.stage}'`,
      source: "Monoco Logic",
      code: "logic-lifecycle",
    };
    diagnostics.push(diagnostic);
  }

  // "status: backlog -> stage: freezed"
  if (data.status === "backlog" && data.stage !== "freezed") {
    const stageLine = findLineOfKey(frontmatterContent, "stage");
    const range = getRangeForLine(textDocument, stageLine, 3);

    const diagnostic: Diagnostic = {
      severity: DiagnosticSeverity.Error,
      range: range,
      message: `Invalid state: If status is 'backlog', stage must be 'freezed'.`,
      source: "Monoco Logic",
      code: "logic-lifecycle",
    };
    diagnostics.push(diagnostic);
  }

  connection.sendDiagnostics({ uri: textDocument.uri, diagnostics });
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
connection.onRequest("monoco/getAllIssues", () => {
  return indexer.getAll();
});

connection.onRequest(
  "monoco/updateIssue",
  async (params: { id: string; changes: any }) => {
    const issue = indexer.get(params.id);
    if (!issue) return { success: false, error: "Issue not found" };

    // Try to get document from manager (open file)
    let document = documents.get(issue.uri);
    let text = "";

    if (document) {
      text = document.getText();
    } else {
      // Read from disk
      try {
        text = fs.readFileSync(issue.filePath, "utf-8");
        // Create a temporary document instance to help with position calculation
        document = TextDocument.create(issue.uri, "markdown", 0, text);
      } catch (e) {
        return { success: false, error: "Failed to read file" };
      }
    }

    if (!document) {
      return { success: false, error: "Could not load document" };
    }

    const edits: TextEdit[] = [];

    // Simple Regex replacers for now to preserve comments
    for (const [key, value] of Object.entries(params.changes)) {
      // Regex to match "key: value" within the frontmatter
      // We assume frontmatter is at the top.
      const regex = new RegExp(`^${key}:\\s*(.*)$`, "m");
      const match = regex.exec(text);
      if (match) {
        const startOffset = match.index; // 0-based index of match in input string
        const endOffset = startOffset + match[0].length;

        const range = Range.create(
          document.positionAt(startOffset),
          document.positionAt(endOffset)
        );

        edits.push(TextEdit.replace(range, `${key}: ${value}`));
      }
    }

    if (edits.length > 0) {
      const workspaceEdit: WorkspaceEdit = {
        changes: {
          [issue.uri]: edits,
        },
      };
      await connection.workspace.applyEdit(workspaceEdit);

      // Update index immediately (optimistic)
      // Actually, onDidChangeWatchedFiles will trigger re-index, but we can do it here too?
      // No, let the watcher handle it to be consistent.

      return { success: true };
    }

    return { success: false, error: "No changes logic applied" };
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

// Make the text document manager listen on the connection
// for open, change and close text document events
documents.listen(connection);

// Listen on the connection
connection.listen();
