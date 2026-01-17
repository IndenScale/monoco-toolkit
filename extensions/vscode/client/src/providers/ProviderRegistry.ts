/**
 * Provider Registry
 * Centralized provider registration
 */

import * as vscode from "vscode";
import { IssueHoverProvider } from "./IssueHoverProvider";
import { IssueCodeLensProvider } from "./IssueCodeLensProvider";
import { IssueFieldControlProvider } from "./IssueFieldControlProvider";
import { ActionService } from "../services/ActionService";

export class ProviderRegistry {
  constructor(
    private context: vscode.ExtensionContext,
    private actionService: ActionService
  ) {}

  /**
   * Register all providers
   */
  registerAll(): IssueFieldControlProvider {
    const issueFieldControl = this.registerFieldControlProvider();
    this.registerHoverProvider();
    this.registerCodeLensProvider();
    return issueFieldControl;
  }

  /**
   * Register hover provider
   */
  private registerHoverProvider(): void {
    this.context.subscriptions.push(
      vscode.languages.registerHoverProvider(
        { scheme: "file", language: "markdown" },
        new IssueHoverProvider(this.actionService)
      )
    );
  }

  /**
   * Register CodeLens provider
   */
  private registerCodeLensProvider(): void {
    this.context.subscriptions.push(
      vscode.languages.registerCodeLensProvider(
        { scheme: "file", language: "markdown" },
        new IssueCodeLensProvider()
      )
    );
  }

  /**
   * Register field control provider (Status/Stage)
   */
  private registerFieldControlProvider(): IssueFieldControlProvider {
    const provider = new IssueFieldControlProvider();
    this.context.subscriptions.push(
      vscode.languages.registerDocumentLinkProvider(
        { scheme: "file", language: "markdown" },
        provider
      )
    );
    return provider;
  }
}
