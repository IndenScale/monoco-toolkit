/**
 * Provider Registry
 * Centralized provider registration
 */

import * as vscode from 'vscode'

// import { IssueCodeLensProvider } from "./IssueCodeLensProvider";
import { IssueFieldControlProvider } from './IssueFieldControlProvider'

export class ProviderRegistry {
  constructor(private context: vscode.ExtensionContext) {}

  /**
   * Register all providers
   */
  registerAll(): IssueFieldControlProvider {
    const issueFieldControl = this.registerFieldControlProvider()

    this.registerCodeLensProvider()
    return issueFieldControl
  }

  /**
   * Register hover provider
   */

  /**
   * Register CodeLens provider
   */
  private registerCodeLensProvider(): void {
    // Moved to LSP Server
    // this.context.subscriptions.push(
    //   vscode.languages.registerCodeLensProvider(
    //     { scheme: "file", language: "markdown" },
    //     new IssueCodeLensProvider()
    //   )
    // );
  }

  /**
   * Register field control provider (Status/Stage)
   */
  private registerFieldControlProvider(): IssueFieldControlProvider {
    const provider = new IssueFieldControlProvider()
    this.context.subscriptions.push(
      vscode.languages.registerDocumentLinkProvider(
        { scheme: 'file', language: 'markdown' },
        provider
      )
    )
    return provider
  }
}
