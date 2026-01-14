import * as vscode from "vscode";

/**
 * Represents a parsed Issue file's YAML front matter
 */
export interface IssueMetadata {
  id: string;
  type: "epic" | "feature" | "fix" | "chore";
  status: "open" | "closed" | "backlog";
  stage?: "todo" | "doing" | "review" | "done";
  title: string;
  parent?: string;
  dependencies?: string[];
  related?: string[];
  tags?: string[];
  created_at?: string;
  opened_at?: string;
  updated_at?: string;
  closed_at?: string;
  solution?: string;
}

/**
 * Represents the location of a field in the document
 */
export interface FieldLocation {
  field: string;
  line: number;
  range: vscode.Range;
  value: any;
}

/**
 * Parser for Monoco Issue files
 */
export class IssueParser {
  /**
   * Check if a file is a valid Monoco Issue file
   */
  static isIssueFile(uri: vscode.Uri): boolean {
    // Must be in Issues/ directory
    if (!uri.fsPath.includes("/Issues/")) {
      return false;
    }

    // Must match Issue file naming pattern
    const fileName = uri.fsPath.split("/").pop() || "";
    return /^(EPIC|FEAT|FIX|CHORE)-\d+.*\.md$/.test(fileName);
  }

  /**
   * Parse YAML front matter from a document
   */
  static parseYaml(document: vscode.TextDocument): IssueMetadata | null {
    const text = document.getText();

    // Match YAML front matter (between --- markers)
    const yamlMatch = text.match(/^---\n([\s\S]*?)\n---/);
    if (!yamlMatch) {
      return null;
    }

    const yamlText = yamlMatch[1];
    const metadata: any = {};

    // Simple YAML parser (handles our specific format)
    const lines = yamlText.split("\n");
    for (const line of lines) {
      // Handle simple key: value
      const simpleMatch = line.match(/^(\w+):\s*(.*)$/);
      if (simpleMatch) {
        const [, key, value] = simpleMatch;

        // Parse arrays (e.g., dependencies: [])
        if (value.startsWith("[") && value.endsWith("]")) {
          const arrayContent = value.slice(1, -1).trim();
          metadata[key] = arrayContent
            ? arrayContent.split(",").map((s) => s.trim())
            : [];
        }
        // Parse quoted strings
        else if (value.startsWith("'") && value.endsWith("'")) {
          metadata[key] = value.slice(1, -1);
        }
        // Parse plain values
        else {
          metadata[key] = value || undefined;
        }
      }
    }

    // Validate required fields
    if (!metadata.id || !metadata.type || !metadata.status) {
      return null;
    }

    // Validate ID format
    if (!/^(EPIC|FEAT|FIX|CHORE)-\d+$/.test(metadata.id)) {
      return null;
    }

    // Validate type
    if (!["epic", "feature", "fix", "chore"].includes(metadata.type)) {
      return null;
    }

    return metadata as IssueMetadata;
  }

  /**
   * Find field locations in the document for CodeLens
   */
  static findFieldLocations(document: vscode.TextDocument): FieldLocation[] {
    const text = document.getText();
    const yamlMatch = text.match(/^---\n([\s\S]*?)\n---/);

    if (!yamlMatch) {
      return [];
    }

    const locations: FieldLocation[] = [];
    const yamlText = yamlMatch[1];
    const lines = yamlText.split("\n");

    lines.forEach((line, index) => {
      const match = line.match(/^(\w+):\s*(.*)$/);
      if (match) {
        const [, field, value] = match;

        // Line number in document (account for opening --- and 0-indexing)
        const lineNumber = index + 1;
        const range = new vscode.Range(lineNumber, 0, lineNumber, line.length);

        // Parse value
        let parsedValue: any = value;
        if (value.startsWith("[") && value.endsWith("]")) {
          const arrayContent = value.slice(1, -1).trim();
          parsedValue = arrayContent
            ? arrayContent.split(",").map((s) => s.trim())
            : [];
        } else if (value.startsWith("'") && value.endsWith("'")) {
          parsedValue = value.slice(1, -1);
        }

        locations.push({
          field,
          line: lineNumber,
          range,
          value: parsedValue,
        });
      }
    });

    return locations;
  }

  /**
   * Validate if a document is a valid Issue file (combines path and content checks)
   */
  static isValidIssueDocument(document: vscode.TextDocument): boolean {
    if (!this.isIssueFile(document.uri)) {
      return false;
    }

    const metadata = this.parseYaml(document);
    return metadata !== null;
  }
}
