import * as vscode from 'vscode'
import * as cp from 'child_process'
import * as path from 'path'
import {
  resolveMonocoExecutable as sharedResolveMonocoExecutable,
  isCommandAvailable as sharedIsCommandAvailable,
} from '../../shared/utils'

// Export system wrapper for testing
export const sys = {
  exec: cp.exec,
}

export function getBundledBinaryPath(context: vscode.ExtensionContext): string {
  const isWindows = process.platform === 'win32'
  const binaryName = isWindows ? 'monoco.exe' : 'monoco'
  return context.asAbsolutePath(path.join('bin', binaryName))
}

/**
 * Resolve Monoco executable path
 * Uses shared resolver with VSCode-specific configuration
 */
export async function resolveMonocoExecutable(context?: vscode.ExtensionContext): Promise<string> {
  const config = vscode.workspace.getConfiguration('monoco')
  const configuredPath = config.get<string>('executablePath') || 'monoco'
  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath
  const bundledPath = context ? getBundledBinaryPath(context) : undefined

  return sharedResolveMonocoExecutable({
    workspaceRoot,
    configuredPath,
    bundledPath,
  })
}

export async function checkAndBootstrap(context: vscode.ExtensionContext) {
  // 1. Check if monoco is already available (including dev version)
  const executable = await resolveMonocoExecutable(context)

  if (await isCommandAvailable(executable, '--help')) {
    return
  }

  // 2. Monoco not found. Check if uv is available.
  const hasUv = await isCommandAvailable('uv')

  if (hasUv) {
    // Scenario A: uv exists, just install toolkit
    const selection = await vscode.window.showInformationMessage(
      'Monoco Toolkit CLI is missing. Install it via uv?',
      'Install',
      'Cancel'
    )
    if (selection === 'Install') {
      await installMonocoToolkit()
    }
  } else {
    // Scenario B: uv missing. Install uv first.
    const selection = await vscode.window.showWarningMessage(
      "Monoco Toolkit requires 'uv' (Fast Python Pkg Mgr). Install 'uv' + Toolkit?",
      'Install All',
      'Cancel'
    )
    if (selection === 'Install All') {
      await installUvAndToolkit()
    }
  }
}

/**
 * Check if a command is available
 * Wrapper around shared utility with VSCode-specific exec function
 */
async function isCommandAvailable(cmd: string, flag: string = '--version'): Promise<boolean> {
  return sharedIsCommandAvailable(cmd, flag, sys.exec)
}

async function installMonocoToolkit() {
  const terminal = getInstallerTerminal()
  terminal.show()
  terminal.sendText('uv tool install monoco-toolkit')
}

async function installUvAndToolkit() {
  const terminal = getInstallerTerminal()
  terminal.show()

  if (process.platform === 'win32') {
    // Windows: Install uv then Monoco
    // We use ; to separate commands in PS or && if acceptable, but sendText implies separate lines or chained.
    // Let's chain them.
    terminal.sendText(
      'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'
    )
    // We assume uv is added to path or we try to use it. Windows environment update in same terminal is hard.
    // It's safer to tell users.
    terminal.sendText('Write-Host "Installing Monoco Toolkit..."')
    // Try to assume default install path or just run it hoping alias works (often requires restart)
    terminal.sendText('uv tool install monoco-toolkit')
  } else {
    // macOS / Linux
    // 1. Install uv
    terminal.sendText('curl -LsSf https://astral.sh/uv/install.sh | sh')

    // 2. Install Monoco using the likely path of uv (since PATH needs shell restart)
    // uv default install location: ~/.local/bin/uv (or $HOME/.cargo/bin sometimes for older scripts, but uv is standalone now)
    // The script outputs where it installed.
    // We try to run explicitly from ~/.local/bin/uv
    const installCmd = `~/.local/bin/uv tool install monoco-toolkit`

    terminal.sendText(`echo "Attempting to install Monoco Toolkit..."`)
    // We try the direct path, if that fails, we fallback to requesting user restart.
    terminal.sendText(
      `${installCmd} || echo "Please restart your terminal to load 'uv', then run: uv tool install monoco-toolkit"`
    )
  }
}

function getInstallerTerminal(): vscode.Terminal {
  let terminal = vscode.window.terminals.find((t) => t.name === 'Monoco Installer')
  if (!terminal) {
    terminal = vscode.window.createTerminal({
      name: 'Monoco Installer',
      iconPath: new vscode.ThemeIcon('cloud-download'),
    })
  }
  return terminal
}
