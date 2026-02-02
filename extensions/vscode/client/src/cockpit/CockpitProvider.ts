/**
 * Cockpit Settings Webview Provider
 * Manages the React-based settings webview panel
 */

import * as vscode from 'vscode'
import {
  CockpitSettings,
  DEFAULT_COCKPIT_SETTINGS,
  WebviewMessage,
  ExtensionMessage,
} from './types'

export class CockpitProvider {
  public static readonly viewType = 'monoco.cockpitSettings'
  private panel?: vscode.WebviewPanel
  private disposables: vscode.Disposable[] = []

  constructor(private readonly extensionUri: vscode.Uri) {}

  /**
   * Show the Cockpit settings panel
   */
  public show(): void {
    if (this.panel) {
      this.panel.reveal(vscode.ViewColumn.One)
      return
    }

    this.panel = vscode.window.createWebviewPanel(
      CockpitProvider.viewType,
      'Monoco Cockpit',
      vscode.ViewColumn.One,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
        localResourceRoots: [this.extensionUri],
      }
    )

    this.panel.webview.html = this.getHtmlForWebview()
    this.panel.iconPath = vscode.Uri.joinPath(this.extensionUri, 'media', 'icon.svg')

    // Handle messages from webview
    this.panel.webview.onDidReceiveMessage(
      (message: WebviewMessage) => this.handleMessage(message),
      null,
      this.disposables
    )

    // Clean up on dispose
    this.panel.onDidDispose(
      () => {
        this.panel = undefined
        this.disposables.forEach((d) => d.dispose())
        this.disposables = []
      },
      null,
      this.disposables
    )
  }

  /**
   * Handle messages from the webview
   */
  private async handleMessage(message: WebviewMessage): Promise<void> {
    console.log('[Cockpit] Received message:', message.type)

    switch (message.type) {
      case 'cockpit:ready':
        // Webview is ready, send initial data
        this.sendSettings()
        break

      case 'cockpit:settings:load':
        this.sendSettings()
        break

      case 'cockpit:settings:save': {
        const savePayload = message.payload as { settings: CockpitSettings }
        await this.saveSettings(savePayload.settings)
        break
      }

      case 'cockpit:settings:preview': {
        const previewPayload = message.payload as { settings: CockpitSettings }
        this.sendCliPreview(previewPayload.settings)
        break
      }

      case 'cockpit:skills:scan': {
        const scanPayload = message.payload as { directory: string }
        await this.scanSkills(scanPayload.directory)
        break
      }
    }
  }

  /**
   * Send settings to webview
   */
  private async sendSettings(): Promise<void> {
    const settings = await this.loadSettings()
    const providers = this.getAvailableProviders()
    const skills = await this.getAvailableSkills()

    this.postMessage({
      type: 'cockpit:settings:loaded',
      payload: {
        settings,
        availableProviders: providers,
        availableSkills: skills,
      },
    })
  }

  /**
   * Load settings from VS Code configuration
   */
  private async loadSettings(): Promise<CockpitSettings> {
    const config = vscode.workspace.getConfiguration('monoco.cockpit')

    return {
      runtime: {
        provider: config.get('runtime.provider', DEFAULT_COCKPIT_SETTINGS.runtime.provider),
        role: config.get('runtime.role', DEFAULT_COCKPIT_SETTINGS.runtime.role),
        autonomy: {
          level: config.get(
            'runtime.autonomy.level',
            DEFAULT_COCKPIT_SETTINGS.runtime.autonomy.level
          ),
          persistence: config.get(
            'runtime.autonomy.persistence',
            DEFAULT_COCKPIT_SETTINGS.runtime.autonomy.persistence
          ),
        },
      },
      capabilities: {
        skills: {
          directory: config.get(
            'capabilities.skills.directory',
            DEFAULT_COCKPIT_SETTINGS.capabilities.skills.directory
          ),
          sets: config.get('capabilities.skills.sets', []),
        },
        systemAccess: {
          enabled: config.get(
            'capabilities.systemAccess.enabled',
            DEFAULT_COCKPIT_SETTINGS.capabilities.systemAccess.enabled
          ),
          allowNetwork: config.get(
            'capabilities.systemAccess.allowNetwork',
            DEFAULT_COCKPIT_SETTINGS.capabilities.systemAccess.allowNetwork
          ),
          allowFileSystem: config.get(
            'capabilities.systemAccess.allowFileSystem',
            DEFAULT_COCKPIT_SETTINGS.capabilities.systemAccess.allowFileSystem
          ),
          allowSystemCommands: config.get(
            'capabilities.systemAccess.allowSystemCommands',
            DEFAULT_COCKPIT_SETTINGS.capabilities.systemAccess.allowSystemCommands
          ),
          restrictedCommands: config.get(
            'capabilities.systemAccess.restrictedCommands',
            DEFAULT_COCKPIT_SETTINGS.capabilities.systemAccess.restrictedCommands
          ),
        },
      },
      culture: {
        language: config.get('culture.language', DEFAULT_COCKPIT_SETTINGS.culture.language),
        tone: config.get('culture.tone', DEFAULT_COCKPIT_SETTINGS.culture.tone),
        responseStyle: config.get(
          'culture.responseStyle',
          DEFAULT_COCKPIT_SETTINGS.culture.responseStyle
        ),
      },
    }
  }

  /**
   * Save settings to VS Code configuration
   */
  private async saveSettings(settings: CockpitSettings): Promise<void> {
    const config = vscode.workspace.getConfiguration('monoco.cockpit')

    await config.update('runtime.provider', settings.runtime.provider, true)
    await config.update('runtime.role', settings.runtime.role, true)
    await config.update('runtime.autonomy.level', settings.runtime.autonomy.level, true)
    await config.update('runtime.autonomy.persistence', settings.runtime.autonomy.persistence, true)

    await config.update('capabilities.skills.directory', settings.capabilities.skills.directory, true)
    await config.update('capabilities.skills.sets', settings.capabilities.skills.sets, true)

    await config.update('capabilities.systemAccess.enabled', settings.capabilities.systemAccess.enabled, true)
    await config.update('capabilities.systemAccess.allowNetwork', settings.capabilities.systemAccess.allowNetwork, true)
    await config.update('capabilities.systemAccess.allowFileSystem', settings.capabilities.systemAccess.allowFileSystem, true)
    await config.update('capabilities.systemAccess.allowSystemCommands', settings.capabilities.systemAccess.allowSystemCommands, true)
    await config.update('capabilities.systemAccess.restrictedCommands', settings.capabilities.systemAccess.restrictedCommands, true)

    await config.update('culture.language', settings.culture.language, true)
    await config.update('culture.tone', settings.culture.tone, true)
    await config.update('culture.responseStyle', settings.culture.responseStyle, true)

    // Notify webview of successful save
    this.postMessage({
      type: 'cockpit:settings:saved',
      payload: { success: true },
    })

    vscode.window.showInformationMessage('Monoco Cockpit settings saved successfully!')
  }

  /**
   * Get available providers
   */
  private getAvailableProviders(): string[] {
    // In a real implementation, this would query the monoco CLI for available providers
    return ['kimi', 'vertex-ai', 'openai', 'anthropic', 'local']
  }

  /**
   * Get available skills
   */
  private async getAvailableSkills(): Promise<Array<{ id: string; name: string; description: string }>> {
    // In a real implementation, this would scan the skills directory
    return [
      { id: 'skill-creator', name: 'Skill Creator', description: 'Create and manage custom skills' },
      { id: 'code-review', name: 'Code Review', description: 'Automated code review capabilities' },
      { id: 'documentation', name: 'Documentation', description: 'Generate and maintain documentation' },
    ]
  }

  /**
   * Scan skills directory
   */
  private async scanSkills(directory: string): Promise<void> {
    // In a real implementation, this would scan the directory and update available skills
    vscode.window.showInformationMessage(`Scanning skills directory: ${directory}`)
  }

  /**
   * Send CLI preview
   */
  private sendCliPreview(settings: CockpitSettings): void {
    const args: string[] = []

    // Build CLI args from settings
    args.push('--provider', settings.runtime.provider)

    if (settings.runtime.role !== 'default') {
      args.push('--role', settings.runtime.role)
    }

    if (settings.runtime.autonomy.level === 'yolo') {
      args.push('--yolo')
    } else if (settings.runtime.autonomy.level === 'full-manual') {
      args.push('--manual-approval')
    }

    if (settings.runtime.autonomy.persistence !== 'unlimited') {
      args.push('--persistence', settings.runtime.autonomy.persistence)
    }

    if (settings.capabilities.skills.directory) {
      args.push('--skills-dir', settings.capabilities.skills.directory)
    }

    const enabledSkills = settings.capabilities.skills.sets.filter((s) => s.enabled).map((s) => s.id)
    if (enabledSkills.length > 0) {
      args.push('--skills', enabledSkills.join(','))
    }

    if (!settings.capabilities.systemAccess.enabled) {
      args.push('--no-system-access')
    }

    if (settings.culture.language !== 'auto') {
      args.push('--lang', settings.culture.language)
    }

    this.postMessage({
      type: 'cockpit:cli:preview',
      payload: { args },
    })
  }

  /**
   * Post message to webview
   */
  private postMessage(message: ExtensionMessage): void {
    this.panel?.webview.postMessage(message)
  }

  /**
   * Generate HTML for webview
   */
  private getHtmlForWebview(): string {
    const webview = this.panel!.webview
    const cockpitPath = vscode.Uri.joinPath(this.extensionUri, 'client', 'out', 'cockpit')

    // Get URIs for built files
    const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(cockpitPath, 'index.js'))
    const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(cockpitPath, 'cockpit.css'))

    // Content Security Policy
    const nonce = this.getNonce()
    const csp = [
      "default-src 'none'",
      `style-src ${webview.cspSource} 'unsafe-inline'`,
      `script-src ${webview.cspSource} 'nonce-${nonce}'`,
      `connect-src ${webview.cspSource} http://localhost:* http://127.0.0.1:*`,
      `img-src ${webview.cspSource} https: data:`,
      "font-src 'self'",
    ].join('; ')

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="${csp}">
  <title>Monoco Cockpit</title>
  <link rel="stylesheet" href="${styleUri}">
</head>
<body>
  <div id="root"></div>
  <script type="module" src="${scriptUri}" nonce="${nonce}"></script>
</body>
</html>`
  }

  /**
   * Generate a nonce for CSP
   */
  private getNonce(): string {
    let text = ''
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    for (let i = 0; i < 32; i++) {
      text += possible.charAt(Math.floor(Math.random() * possible.length))
    }
    return text
  }

  /**
   * Dispose the provider
   */
  public dispose(): void {
    this.panel?.dispose()
    this.disposables.forEach((d) => d.dispose())
  }
}
