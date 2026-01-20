/**
 * TreeView Commands
 * Commands for controlling the native TreeView
 */

import * as vscode from 'vscode'
import { IssueTreeProvider } from '../views/IssueTreeProvider'
import { LanguageClientManager } from '../lsp/LanguageClientManager'

export class TreeViewCommands {
  constructor(
    private context: vscode.ExtensionContext,
    private treeProvider: IssueTreeProvider,
    private lspManager: LanguageClientManager
  ) {}

  /**
   * Register all TreeView commands
   */
  registerAll(): void {
    this.registerSelectProject()
    this.registerSearch()
    this.registerRefresh()
  }

  /**
   * Command: Select Project
   * Shows a QuickPick to select active project filter
   */
  private registerSelectProject(): void {
    this.context.subscriptions.push(
      vscode.commands.registerCommand('monoco.selectProject', async () => {
        try {
          const metadata: any = await this.lspManager.sendRequest('monoco/getMetadata')
          const projects = metadata.projects || []

          const items: vscode.QuickPickItem[] = [
            {
              label: '$(globe) All Projects',
              description: 'Show issues from all projects',
              detail: 'all',
            },
            ...projects.map((p: any) => ({
              label: `$(folder) ${p.name || p.id}`,
              description: p.id,
              detail: p.id,
            })),
          ]

          const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select a project to filter issues',
            matchOnDescription: true,
          })

          if (selected) {
            const projectId = selected.detail || 'all'
            this.treeProvider.setProject(projectId)
            vscode.window.showInformationMessage(`Switched to: ${selected.label}`)
          }
        } catch (e) {
          vscode.window.showErrorMessage('Failed to load projects: ' + (e as Error).message)
        }
      })
    )
  }

  /**
   * Command: Search Issues
   * Shows an input box to search/filter issues
   */
  private registerSearch(): void {
    this.context.subscriptions.push(
      vscode.commands.registerCommand('monoco.searchIssues', async () => {
        const query = await vscode.window.showInputBox({
          placeHolder: 'Search issues by title or ID...',
          prompt: 'Enter search query (leave empty to clear filter)',
        })

        if (query !== undefined) {
          this.treeProvider.setSearchQuery(query)
          if (query) {
            vscode.window.showInformationMessage(`Filtering by: "${query}"`)
          } else {
            vscode.window.showInformationMessage('Search filter cleared')
          }
        }
      })
    )
  }

  /**
   * Command: Refresh TreeView
   * Manually refresh the issue tree
   */
  private registerRefresh(): void {
    this.context.subscriptions.push(
      vscode.commands.registerCommand('monoco.refreshTreeView', async () => {
        try {
          const issues: any[] = await this.lspManager.sendRequest('monoco/getAllIssues')
          this.treeProvider.updateIssues(issues)
          vscode.window.showInformationMessage('Issues refreshed')
        } catch (e) {
          vscode.window.showErrorMessage('Failed to refresh: ' + (e as Error).message)
        }
      })
    )
  }
}
