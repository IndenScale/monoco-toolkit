/**
 * Monoco Kanban Webview Provider
 * Manages the kanban board webview and its communication with the extension
 */

import * as path from 'path'
import * as fs from 'fs'
import * as vscode from 'vscode'
import { VIEW_TYPES, MESSAGE_TYPES } from '@shared/constants'
import { WebviewMessage, ExtensionMessage } from '@shared/types'
import { LanguageClientManager } from '../lsp/LanguageClientManager'

export class KanbanProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = VIEW_TYPES.KANBAN
  private view?: vscode.WebviewView

  constructor(
    private readonly extensionUri: vscode.Uri,
    private readonly lspManager: LanguageClientManager,
    private readonly runMonoco: (args: string[], cwd?: string) => Promise<string>,

    private readonly outputChannel: vscode.OutputChannel
  ) {}

  public resolveWebviewView(webviewView: vscode.WebviewView) {
    this.view = webviewView
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.extensionUri],
    }

    webviewView.webview.onDidReceiveMessage((data: WebviewMessage) => this.handleMessage(data))
    webviewView.webview.html = this.getHtmlForWebview()
  }

  /**
   * Handle messages from webview
   */
  private async handleMessage(data: WebviewMessage): Promise<void> {
    this.outputChannel.appendLine(`[Extension] Received message from webview: ${data.type}`)

    switch (data.type) {
      case MESSAGE_TYPES.GET_LOCAL_DATA:
        await this.handleGetLocalData()
        break

      case MESSAGE_TYPES.SAVE_STATE:
        await this.handleSaveState(data.key, data.value)
        break

      case MESSAGE_TYPES.UPDATE_ISSUE:
        await this.handleUpdateIssue(data.issueId, data.changes)
        break

      case MESSAGE_TYPES.CREATE_ISSUE:
        await this.handleCreateIssue(data.value)
        break

      case MESSAGE_TYPES.OPEN_ISSUE_FILE:
        await this.handleOpenIssueFile(data.value.path)
        break

      case MESSAGE_TYPES.OPEN_FILE:
        await this.handleOpenFile(
          data.path || data.value?.path,
          data.line || data.value?.line,
          data.column || data.value?.column
        )
        break

      case MESSAGE_TYPES.UPDATE_CONFIG:
        await this.runMonoco(['config', 'set', data.value.key, data.value.value])
        break

      case MESSAGE_TYPES.OPEN_URL:
        await this.handleOpenUrl(data.url)
        break
    }
  }

  /**
   * Get local data (issues and metadata)
   */
  private async handleGetLocalData(): Promise<void> {
    try {
      this.outputChannel.appendLine('[Extension] handleGetLocalData called')
      const client = this.lspManager.getClient()
      if (!client) {
        this.outputChannel.appendLine('[Extension] LSP Client not ready yet')
        return
      }

      this.outputChannel.appendLine('[Extension] Requesting issues from LSP...')
      const issues: any[] = await this.lspManager.sendRequest('monoco/getAllIssues')
      this.outputChannel.appendLine(`[Extension] Received issues from LSP: ${issues.length}`)

      this.outputChannel.appendLine('[Extension] Requesting metadata from LSP...')
      const metadata: any = await this.lspManager.sendRequest('monoco/getMetadata')
      this.outputChannel.appendLine(
        `[Extension] Received metadata: ${JSON.stringify(metadata).substring(0, 200)}`
      )

      this.outputChannel.appendLine(
        `[Extension] Data fetched: ${issues.length} issues, ${metadata.projects?.length} projects`
      )

      const dataPayload = {
        issues,
        projects: metadata.projects,
        workspaceState: {
          last_active_project_id: metadata.last_active_project_id,
        },
      }
      this.outputChannel.appendLine(
        `[Extension] Sending DATA_UPDATED: ${dataPayload.issues.length} issues, ${dataPayload.projects?.length} projects`
      )

      this.postMessage({
        type: MESSAGE_TYPES.DATA_UPDATED,
        payload: dataPayload,
      })

      this.outputChannel.appendLine('[Extension] Messages posted to webview')
    } catch (e) {
      this.outputChannel.appendLine(`[Extension] handleGetLocalData: LSP Request Failed - ${e}`)
    }
  }

  /**
   * Save state to workspace
   */
  private async handleSaveState(key: string, value: any): Promise<void> {
    if (key === 'last_active_project_id') {
      const wsFolder = vscode.workspace.workspaceFolders?.[0]
      if (wsFolder) {
        const statePath = path.join(wsFolder.uri.fsPath, '.monoco', 'state.json')
        try {
          let current = {}
          if (fs.existsSync(statePath)) {
            current = JSON.parse(fs.readFileSync(statePath, 'utf-8'))
          }
          const updated = {
            ...current,
            last_active_project_id: value,
          }
          fs.writeFileSync(statePath, JSON.stringify(updated, null, 2))
        } catch (e) {
          console.error('Failed to save state.json', e)
        }
      }
    }
  }

  /**
   * Update issue via LSP
   */
  private async handleUpdateIssue(issueId: string, changes: any): Promise<void> {
    await this.lspManager.sendRequest('monoco/updateIssue', {
      id: issueId,
      changes,
    })
  }

  /**
   * Create new issue
   */
  private async handleCreateIssue(value: {
    title: string
    type: string
    parent?: string
  }): Promise<void> {
    const { title, type, parent } = value
    const args = ['issue', 'create', type, '--title', title, '--json']
    if (parent) {
      args.push('--parent', parent)
    }

    try {
      const output = await this.runMonoco(args)
      const result = JSON.parse(output)

      let filePath = result.issue?.path || result.path

      if (filePath) {
        const wsFolder = vscode.workspace.workspaceFolders?.[0]
        if (wsFolder) {
          const uri = path.isAbsolute(filePath)
            ? vscode.Uri.file(filePath)
            : vscode.Uri.joinPath(wsFolder.uri, filePath)

          const doc = await vscode.workspace.openTextDocument(uri)
          await vscode.window.showTextDocument(doc, { preview: true })
        }
      }
    } catch (e: any) {
      vscode.window.showErrorMessage('Failed to create issue: ' + e.message)
      console.error(e)
    }
  }

  /**
   * Open issue file
   */
  private async handleOpenIssueFile(filePath: string): Promise<void> {
    await this.handleOpenFile(filePath)
  }

  /**
   * Open file at specific line and column
   */
  private async handleOpenFile(filePath?: string, line?: number, column?: number): Promise<void> {
    if (!filePath) {
      return
    }

    try {
      const wsFolder = vscode.workspace.workspaceFolders?.[0]
      const uri = path.isAbsolute(filePath)
        ? vscode.Uri.file(filePath)
        : wsFolder
          ? vscode.Uri.joinPath(wsFolder.uri, filePath)
          : vscode.Uri.file(filePath)

      const doc = await vscode.workspace.openTextDocument(uri)
      const editor = await vscode.window.showTextDocument(doc, {
        preview: true,
      })

      if (line !== undefined && line > 0) {
        const pos = new vscode.Position(
          line - 1,
          column !== undefined && column > 0 ? column - 1 : 0
        )
        editor.selection = new vscode.Selection(pos, pos)
        editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter)
      }
    } catch (e) {
      vscode.window.showErrorMessage(`Could not open file: ${filePath}`)
    }
  }

  /**
   * Open URL in external browser
   */
  private async handleOpenUrl(url: string): Promise<void> {
    if (url) {
      vscode.env.openExternal(vscode.Uri.parse(url))
    }
  }

  /**
   * Generate HTML for webview
   */
  private getHtmlForWebview(): string {
    const webviewPath = vscode.Uri.joinPath(this.extensionUri, 'client', 'out', 'webview')

    const indexUri = vscode.Uri.joinPath(webviewPath, 'index.html')

    // Add cache-busting timestamp
    const cacheBuster = Date.now()
    const styleUri = this.view!.webview.asWebviewUri(vscode.Uri.joinPath(webviewPath, 'style.css'))
    const scriptUri = this.view!.webview.asWebviewUri(vscode.Uri.joinPath(webviewPath, 'main.js'))

    // Ensure file exists
    if (!fs.existsSync(indexUri.fsPath)) {
      console.error(`Webview index not found at ${indexUri.fsPath}`)
      return `<html><body><h1>Error: Webview not found</h1></body></html>`
    }

    let html = fs.readFileSync(indexUri.fsPath, 'utf-8')

    const config = vscode.workspace.getConfiguration('monoco')
    const apiBase = config.get('apiBaseUrl') || 'http://127.0.0.1:8642/api/v1'
    const webUrl = config.get('webUrl') || 'http://127.0.0.1:8642'

    // Content Security Policy
    const csp = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${
      this.view!.webview.cspSource
    } 'unsafe-inline'; script-src ${
      this.view!.webview.cspSource
    } 'unsafe-inline'; connect-src http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; img-src ${
      this.view!.webview.cspSource
    } https: data:;">`

    html = html.replace('<head>', `<head>\n${csp}`)

    // Inject configuration
    html = html.replace(
      '<!-- CONFIG_INJECTION -->',
      `<script>
        window.monocoConfig = {
          apiBase: "${apiBase}",
          webUrl: "${webUrl}",
          rootPath: "${vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || ''}"
        };
        console.log("[Webview] Config injected:", window.monocoConfig);
      </script>`
    )

    // Replace asset URLs with cache-busting
    html = html.replace('href="style.css"', `href="${styleUri}?v=${cacheBuster}"`)
    html = html.replace('src="main.js"', `src="${scriptUri}?v=${cacheBuster}"`)

    return html
  }

  /**
   * Post message to webview
   */
  private postMessage(message: ExtensionMessage): void {
    this.view?.webview.postMessage(message)
  }

  /**
   * Refresh webview
   */
  public refresh(): void {
    this.postMessage({ type: MESSAGE_TYPES.REFRESH })
  }

  /**
   * Show create view
   */
  public showCreateView(): void {
    this.postMessage({ type: MESSAGE_TYPES.SHOW_CREATE_VIEW })
  }

  /**
   * Show settings view
   */
  public showSettings(): void {
    this.postMessage({ type: MESSAGE_TYPES.SHOW_SETTINGS })
  }
}
