/**
 * Definition Provider
 * Provides "Go to Definition" functionality for issue links
 */

import { DefinitionParams, Location } from "vscode-languageserver/node";
import { fileURLToPath } from "url";
import { CLIExecutor } from "../services/CLIExecutor";
import { findProjectRoot } from "../utils/helpers";

export class DefinitionProvider {
  private logger?: (message: string) => void;

  constructor(
    private workspaceRoot: string,
    private cliExecutor: CLIExecutor,
    logger?: (message: string) => void
  ) {
    this.logger = logger;
  }

  /**
   * Provide definition for a given position
   */
  async provideDefinition(
    params: DefinitionParams
  ): Promise<Location[] | null> {
    if (!this.workspaceRoot) {
      return null;
    }

    const filePath = fileURLToPath(params.textDocument.uri);
    const root = findProjectRoot(filePath) || this.workspaceRoot;

    try {
      const stdout = await this.cliExecutor.execute(
        [
          "issue",
          "lsp",
          "definition",
          "--file",
          filePath,
          "--line",
          String(params.position.line),
          "--char",
          String(params.position.character),
        ],
        root
      );

      const locations = JSON.parse(stdout);
      if (locations && locations.length > 0) {
        return locations;
      }
    } catch (e: any) {
      this.logError(`Definition failed: ${e.message}`);
    }

    return null;
  }

  /**
   * Log an error
   */
  private logError(message: string) {
    if (this.logger) {
      this.logger(`[Monoco LSP] ${message}`);
    }
  }
}
