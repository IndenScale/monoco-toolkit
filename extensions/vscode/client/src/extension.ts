/**
 * Monoco VSCode Extension Entry Point
 * Refactored to use modular architecture
 */

import { exec } from 'child_process'
import { promisify } from 'util'

import * as vscode from 'vscode'
import { checkAndBootstrap, resolveMonocoExecutable } from './bootstrap'
import { LanguageClientManager } from './lsp/LanguageClientManager'
import { KanbanProvider } from './webview/KanbanProvider'
import { IssueTreeProvider } from './views/IssueTreeProvider'
import { ProviderRegistry } from './providers/ProviderRegistry'
import { CommandRegistry } from './commands/CommandRegistry'
import { VIEW_TYPES } from '../../shared/constants'
import { IssueFilterWebviewProvider } from './views/IssueFilterWebviewProvider'
import { CockpitProvider } from './cockpit/CockpitProvider'

const execAsync = promisify(exec)
let outputChannel: vscode.OutputChannel
let lspManager: LanguageClientManager

/**
 * Execute Monoco CLI command
 */
async function runMonoco(args: string[], cwd?: string): Promise<string> {
  const executable = await resolveMonocoExecutable()

  const workspaceRoot = cwd || vscode.workspace.workspaceFolders?.[0]?.uri.fsPath

  if (!workspaceRoot) {
    throw new Error('No workspace root found')
  }

  // Inject --root parameter for strict context enforcement (FIX-0009)
  const finalArgs = ['--root', workspaceRoot, ...args]

  // Escape args
  const escapedArgs = finalArgs.map((a) => {
    if (/^[\w\d\-_]+$/.test(a)) {
      return a
    }
    return `"${a.replace(/"/g, '\\"')}"`
  })

  const cmd = `${executable} ${escapedArgs.join(' ')}`
  const result = await execAsync(cmd, { cwd: workspaceRoot })
  return result.stdout.trim()
}

/**
 * Check dependencies (uv and monoco)
 */
async function checkDependencies(): Promise<void> {
  outputChannel.appendLine('Checking dependencies...')

  try {
    const uvCheck = await execAsync('uv --version')
    outputChannel.appendLine(`✓ uv version: ${uvCheck.stdout.trim()}`)
  } catch (error) {
    outputChannel.appendLine('✗ uv is not available')
    const installOption = 'Install uv'
    const option = await vscode.window.showErrorMessage(
      'uv is not installed or not in PATH. Would you like to install it?',
      installOption
    )

    if (option === installOption) {
      await vscode.env.openExternal(
        vscode.Uri.parse('https://docs.astral.sh/uv/getting-started/installation/')
      )
    }
  }

  try {
    const executable = await resolveMonocoExecutable()
    const versionResult = await execAsync(`${executable} --version`)
    outputChannel.appendLine(
      `✓ monoco version: ${versionResult.stdout.trim()} (Source: ${executable})`
    )
  } catch (error) {
    outputChannel.appendLine('✗ monoco is not available')
    const installOption = 'Install monoco (Global)'
    const manualOption = 'Manual Install'
    const option = await vscode.window.showErrorMessage(
      'monoco is not found in your environment. Would you like to install it globally via uv?',
      installOption,
      manualOption
    )

    if (option === installOption) {
      try {
        outputChannel.appendLine("Installing monoco via 'uv tool install monoco-toolkit'...")
        await execAsync('uv tool install monoco-toolkit --force')
        outputChannel.appendLine('✓ monoco installed successfully via uv tool')

        const executable = await resolveMonocoExecutable()
        const verifyResult = await execAsync(`${executable} --version`)
        outputChannel.appendLine(`✓ Verified monoco version: ${verifyResult.stdout.trim()}`)
      } catch (installError) {
        outputChannel.appendLine(`✗ Failed to install monoco: ${installError}`)
        vscode.window.showErrorMessage(`Failed to install monoco: ${installError}`)
      }
    } else if (option === manualOption) {
      await vscode.env.openExternal(vscode.Uri.parse('https://github.com/IndenScale/Monoco'))
    }
  }
}

/**
 * Activate extension
 */
export async function activate(context: vscode.ExtensionContext) {
  outputChannel = vscode.window.createOutputChannel('Monoco')
  outputChannel.appendLine('Monoco extension activated!')

  // 4. Start LSP client
  lspManager = new LanguageClientManager(context, outputChannel)

  // 5. Initialize services

  const kanbanProvider = new KanbanProvider(
    context.extensionUri,
    lspManager,
    runMonoco,
    outputChannel
  )

  // 5.1 Initialize Native TreeView Provider
  const issueTreeProvider = new IssueTreeProvider()
  const treeView = vscode.window.createTreeView('monoco.issueTreeView', {
    treeDataProvider: issueTreeProvider,
    showCollapseAll: true,
    canSelectMany: false,
    dragAndDropController: issueTreeProvider,
  })
  context.subscriptions.push(treeView)

  // 5.2 Initialize Filter Webview Provider
  const issueFilterProvider = new IssueFilterWebviewProvider(context.extensionUri)
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider('monoco.issueFilterView', issueFilterProvider)
  )

  // Handle filter selection from Webview
  issueFilterProvider.onDidUpdateFilter((state: any) => {
    issueTreeProvider.setFilter(state)
  })

  // Register command to open issue and expand tree
  context.subscriptions.push(
    vscode.commands.registerCommand('monoco.openIssueAndExpand', async (item) => {
      if (item && item.issue && item.issue.path) {
        // 1. Open document
        await vscode.commands.executeCommand('vscode.open', vscode.Uri.file(item.issue.path))
        // 2. Expand in tree
        try {
          await treeView.reveal(item, {
            expand: true,
            focus: false,
            select: true,
          })
        } catch (e) {
          // Ignore reveal errors (e.g. if item not visible)
        }
      }
    })
  )

  // Helper function to fetch and update TreeView data
  const updateTreeViewData = async () => {
    try {
      const client = lspManager.getClient()
      if (!client) {
        return
      }

      const issues: any[] = await lspManager.sendRequest('monoco/getAllIssues')
      issueTreeProvider.updateIssues(issues)

      // Also get metadata for filters
      const metadata: any = await lspManager.sendRequest('monoco/getMetadata')
      if (metadata && metadata.projects) {
        issueFilterProvider.setProjects(metadata.projects.map((p: any) => p.id))
      }
    } catch (e) {
      // Silently fail if LSP is not ready
    }
  }

  // Initial data load and periodic refresh
  setTimeout(() => {
    updateTreeViewData()
    setInterval(updateTreeViewData, 10000) // Refresh every 10s
  }, 2000) // Wait 2s for LSP to be ready

  // Background Initialization to prevent blocking activation
  vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Window,
      title: 'Initializing Monoco...',
    },
    async () => {
      try {
        await checkDependencies()
        await lspManager.start()
        // Notify webview that LSP is ready
        kanbanProvider.refresh()
      } catch (err) {
        outputChannel.appendLine(`Initialization failed: ${err}`)
      }
    }
  )

  // 6. Register providers
  const providerRegistry = new ProviderRegistry(context)
  const issueFieldControl = providerRegistry.registerAll()

  // 7. Register commands
  const commandRegistry = new CommandRegistry(context, {
    kanbanProvider,

    issueFieldControl,
    runMonoco,
    checkDependencies,
    treeProvider: issueTreeProvider,
    lspManager,
  })
  commandRegistry.registerAll()

  // 8. Register webview
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(VIEW_TYPES.KANBAN, kanbanProvider)
  )

  // 9. Register Cockpit Settings provider
  const cockpitProvider = new CockpitProvider(context.extensionUri)
  context.subscriptions.push(
    vscode.commands.registerCommand('monoco.openCockpit', () => {
      cockpitProvider.show()
    })
  )

  // 11. Bootstrap dependencies if needed
  checkAndBootstrap(context)
}

/**
 * Deactivate extension
 */
export async function deactivate(): Promise<void> {
  if (lspManager) {
    await lspManager.stop()
  }
}
