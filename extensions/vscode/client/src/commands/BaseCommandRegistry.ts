/**
 * Command Registry
 * Centralized command registration and management
 */

import * as vscode from 'vscode'

export abstract class BaseCommandRegistry {
  protected context: vscode.ExtensionContext

  constructor(context: vscode.ExtensionContext) {
    this.context = context
  }

  /**
   * Register all commands
   */
  abstract registerAll(): void

  /**
   * Register a single command
   */
  protected register(id: string, handler: (...args: any[]) => any, thisArg?: any): void {
    this.context.subscriptions.push(vscode.commands.registerCommand(id, handler, thisArg))
  }
}
