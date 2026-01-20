/**
 * Issue Commands
 * Commands related to issue management
 */

import * as vscode from 'vscode'
import { BaseCommandRegistry } from './BaseCommandRegistry'
import { COMMAND_IDS } from '../../../shared/constants'
import { KanbanProvider } from '../webview/KanbanProvider'

import { IssueFieldControlProvider } from '../providers/IssueFieldControlProvider'
import { parseFrontmatter } from '../utils/frontmatter'

export class IssueCommands extends BaseCommandRegistry {
  constructor(
    context: vscode.ExtensionContext,
    private kanbanProvider: KanbanProvider,

    private issueFieldControl: IssueFieldControlProvider,
    private runMonoco: (args: string[], cwd?: string) => Promise<string>
  ) {
    super(context)
  }

  registerAll(): void {
    this.registerKanbanCommands()
    this.registerIssueEditCommands()
  }

  private registerKanbanCommands(): void {
    this.register(COMMAND_IDS.OPEN_KANBAN, () => {
      vscode.commands.executeCommand('monoco-kanban.focus')
    })

    this.register(COMMAND_IDS.REFRESH_ENTRY, () => {
      this.kanbanProvider.refresh()
    })

    this.register(COMMAND_IDS.CREATE_ISSUE, () => {
      this.kanbanProvider.showCreateView()
    })
  }

  private registerIssueEditCommands(): void {
    this.register(COMMAND_IDS.TOGGLE_STATUS, async (filePath: string, _line: number) => {
      const doc = await vscode.workspace.openTextDocument(filePath)
      const text = doc.getText()
      const meta = parseFrontmatter(text)

      if (!meta.id || !meta.status) {
        vscode.window.showErrorMessage('Could not parse Issue ID or Status.')
        return
      }

      const current = meta.status
      const next = this.issueFieldControl.getNextValue(
        current,
        this.issueFieldControl.getEnumList('status')
      )

      try {
        await this.runMonoco(['issue', 'update', meta.id, '--status', next])
      } catch (e: any) {
        vscode.window.showErrorMessage(`Failed to update status: ${e.message}`)
      }
    })

    this.register(COMMAND_IDS.TOGGLE_STAGE, async (filePath: string, _line: number) => {
      const doc = await vscode.workspace.openTextDocument(filePath)
      const text = doc.getText()
      const meta = parseFrontmatter(text)

      if (!meta.id || !meta.stage) {
        vscode.window.showErrorMessage('Could not parse Issue ID or Stage.')
        return
      }

      const current = meta.stage
      const next = this.issueFieldControl.getNextValue(
        current,
        this.issueFieldControl.getEnumList('stage')
      )

      try {
        await this.runMonoco(['issue', 'update', meta.id, '--stage', next])
      } catch (e: any) {
        vscode.window.showErrorMessage(`Failed to update stage: ${e.message}`)
      }
    })
  }
}
