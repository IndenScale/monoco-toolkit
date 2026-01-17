/**
 * Diagnostic Provider
 * Provides diagnostics (linting) for issue files
 */

import { Diagnostic, DiagnosticSeverity } from "vscode-languageserver/node";
import { TextDocument } from "vscode-languageserver-textdocument";
import { fileURLToPath } from "url";
import { CLIExecutor } from "../services/CLIExecutor";
import { findProjectRoot } from "../utils/helpers";

export class DiagnosticProvider {
  private logger?: (message: string) => void;

  constructor(
    private workspaceRoot: string,
    private cliExecutor: CLIExecutor,
    logger?: (message: string) => void
  ) {
    this.logger = logger;
  }

  /**
   * Validate a text document
   */
  async validate(document: TextDocument): Promise<Diagnostic[]> {
    const diagnostics: Diagnostic[] = [];
    const text = document.getText();

    // Skip non-issue files
    if (!/^---\n([\s\S]*?)\n---/.test(text)) {
      return diagnostics;
    }

    try {
      const filePath = fileURLToPath(document.uri);
      const cliDiagnostics = await this.callCLI(filePath);
      diagnostics.push(...cliDiagnostics);
    } catch (error: any) {
      this.logWarn(`CLI validation failed: ${error.message}`);
    }

    return diagnostics;
  }

  /**
   * Call the Monoco CLI for linting
   */
  private async callCLI(filePath: string): Promise<Diagnostic[]> {
    if (!this.workspaceRoot) {
      return [];
    }

    try {
      const root = findProjectRoot(filePath) || this.workspaceRoot;
      const { stdout, code } = await this.cliExecutor.executeRaw(
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
      this.logWarn(`Lint failed: ${e.message}`);
      return [];
    }
  }

  /**
   * Log a warning
   */
  private logWarn(message: string) {
    if (this.logger) {
      this.logger(`[Monoco LSP] WARN: ${message}`);
    }
  }
}
