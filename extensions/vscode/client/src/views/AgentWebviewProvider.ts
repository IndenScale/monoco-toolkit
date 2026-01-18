import * as vscode from "vscode";
import { AgentStateService } from "../services/AgentStateService";
import { ActionService, AgentAction } from "../services/ActionService";

export interface AgentViewState {
  defaultProvider: string;
  actionProviders: { [actionName: string]: string };
}

export class AgentWebviewProvider implements vscode.WebviewViewProvider {
  private _view?: vscode.WebviewView;
  private actions: AgentAction[] = [];
  private providers: string[] = [];

  // Default State
  private state: AgentViewState = {
    defaultProvider: "gemini",
    actionProviders: {},
  };

  constructor(
    private readonly _extensionUri: vscode.Uri,
    private readonly _agentStateService: AgentStateService,
    private readonly _actionService: ActionService,
  ) {
    // Subscribe to changes
    this._agentStateService.onDidChangeState(() => {
      this.updateData();
    });
    this._actionService.onDidChangeActions(() => {
      this.updateData();
    });

    // Initial fetch
    this.updateData();
  }

  private updateData() {
    this.providers = this._agentStateService.getAvailableProviders();
    this.actions = this._actionService.getActions();
    this.updateWebview();
  }

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ) {
    this._view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri],
    };

    webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

    webviewView.webview.onDidReceiveMessage((data) => {
      switch (data.type) {
        case "updateState":
          this.state = data.value;
          // Apply changes to configuration or persist them
          this.persistState(this.state);
          break;
        case "webviewReady":
          this.updateWebview();
          break;
      }
    });
  }

  private persistState(state: AgentViewState) {
    const config = vscode.workspace.getConfiguration("monoco");

    // Update default provider
    config.update(
      "agent.defaultProvider",
      state.defaultProvider,
      vscode.ConfigurationTarget.Global,
    );

    // Update specific action providers
    // Note: This relies on a config structure that might need to be defined in package.json
    config.update(
      "agent.actionProviders",
      state.actionProviders,
      vscode.ConfigurationTarget.Global,
    );
  }

  private updateWebview() {
    if (this._view) {
      // Create options for providers
      const providerOptions = this.providers.map((p) => ({
        label: p,
        value: p,
      }));

      // Map actions for the view
      const viewActions = this.actions.map((a) => ({
        name: a.name,
        description: a.description,
        provider: this.state.actionProviders[a.name] || "inherit", // logic to get effective provider
      }));

      this._view.webview.postMessage({
        type: "init",
        providers: providerOptions,
        actions: viewActions,
        state: this.state,
      });
    }
  }

  private _getHtmlForWebview(webview: vscode.Webview) {
    const nonce = getNonce();

    return `<!DOCTYPE html>
			<html lang="en">
			<head>
				<meta charset="UTF-8">
				<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<title>Agent Settings</title>
                <style>
                    :root {
                        --dropdown-bg: var(--vscode-dropdown-background);
                        --dropdown-fg: var(--vscode-dropdown-foreground);
                        --dropdown-border: var(--vscode-dropdown-border);
                        --input-bg: var(--vscode-input-background);
                        --input-fg: var(--vscode-input-foreground);
                        --input-border: var(--vscode-input-border);
                        --focus-border: var(--vscode-focusBorder);
                        --hover-bg: var(--vscode-list-hoverBackground);
                    }
                    body { 
                        padding: 0; 
                        font-family: var(--vscode-font-family); 
                        color: var(--vscode-foreground); 
                        font-size: 13px;
                        height: 100vh;
                        margin: 0;
                        overflow-y: auto;
                        display: flex;
                        flex-direction: column;
                    }

                    .main-container {
                        padding: 10px;
                        display: flex;
                        flex-direction: column;
                        gap: 12px;
                    }
                    
                    /* Section Header */
                    .section-header {
                        font-size: 11px;
                        font-weight: bold;
                        text-transform: uppercase;
                        opacity: 0.6;
                        margin-bottom: 4px;
                        margin-top: 8px;
                        border-bottom: 1px solid var(--vscode-widget-border);
                        padding-bottom: 4px;
                    }
                    .section-header:first-child {
                        margin-top: 0;
                    }

                    .filter-row {
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        gap: 10px;
                        margin-bottom: 8px;
                    }

                    .filter-label {
                        font-size: 12px;
                        /* opacity: 0.8; */
                        min-width: 80px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    }

                    /* Custom Dropdown */
                    .dropdown-container {
                        position: relative;
                        flex: 1;
                        min-width: 0;
                    }

                    .dropdown-trigger {
                        background: var(--dropdown-bg);
                        color: var(--dropdown-fg);
                        border: 1px solid var(--dropdown-border);
                        padding: 3px 8px;
                        border-radius: 2px;
                        cursor: pointer;
                        font-size: 12px;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        height: 24px;
                        box-sizing: border-box;
                    }
                    
                    .dropdown-trigger:hover {
                        border-color: var(--focus-border);
                    }

                    .dropdown-trigger:after {
                        content: '';
                        border: 4px solid transparent;
                        border-top-color: currentColor;
                        margin-left: 6px;
                        transform: translateY(2px);
                    }

                    .dropdown-content {
                        display: none;
                        position: absolute;
                        top: 100%;
                        left: 0;
                        right: 0;
                        background: var(--dropdown-bg);
                        border: 1px solid var(--focus-border);
                        z-index: 100;
                        max-height: 200px;
                        overflow-y: auto;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                        margin-top: 1px;
                    }
                    
                    .dropdown-content.show {
                        display: block;
                    }

                    .dropdown-item {
                        padding: 4px 8px;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                    }

                    .dropdown-item:hover {
                        background: var(--hover-bg);
                    }
                    
                    .dropdown-item .check {
                        opacity: 0;
                        width: 14px;
                    }
                    .dropdown-item.checked .check {
                        opacity: 1;
                    }

                    /* Scrollbar */
                    ::-webkit-scrollbar { width: 6px; }
                    ::-webkit-scrollbar-track { background: transparent; }
                    ::-webkit-scrollbar-thumb { background: var(--vscode-scrollbarSlider-background); border-radius: 3px; }
                </style>
			</head>
			<body>
                <div class="main-container">
                    <div class="section-header">Global</div>
                    <div id="default-agent-container"></div>
                    
                    <div class="section-header">Actions</div>
                    <div id="actions-container"></div>
                </div>

				<script nonce="${nonce}">
                    const vscode = acquireVsCodeApi();
                    
                    let state = {
                        defaultProvider: 'gemini',
                        actionProviders: {}
                    };
                    let providers = [];
                    let actions = [];

                    const els = {
                        defaultAgent: document.getElementById('default-agent-container'),
                        actions: document.getElementById('actions-container')
                    };

                    window.addEventListener('message', event => {
                        const message = event.data;
                        switch (message.type) {
                            case 'init':
                                providers = message.providers || [];
                                actions = message.actions || [];
                                state = message.state || state;
                                render();
                                break;
                        }
                    });

                    // Close dropdowns on outside click
                    document.addEventListener('click', (e) => {
                        if (!e.target.closest('.dropdown-container')) {
                            document.querySelectorAll('.dropdown-content').forEach(d => d.classList.remove('show'));
                        }
                    });

                    function render() {
                        // Render Default Agent Selector
                        renderDropdown(
                            els.defaultAgent, 
                            'Default', 
                            providers, 
                            state.defaultProvider, 
                            (val) => {
                                state.defaultProvider = val;
                                updateState();
                                render(); // Re-render to update inherit labels
                            }
                        );

                        // Render Actions
                        els.actions.innerHTML = ''; // Clear
                        actions.forEach(action => {
                            const container = document.createElement('div');
                            els.actions.appendChild(container);
                            
                            // Construct options including "Inherit"
                            // If user explicitly set it, use that value. If not, it's 'inherit' (or undefined/null in state)
                            // But for the dropdown, we need to show the effective choice.
                            
                            const currentVal = state.actionProviders[action.name] || 'inherit';
                            
                            const actionOptions = [
                                { label: \`Inherit (\${state.defaultProvider})\`, value: 'inherit' },
                                ...providers
                            ];

                            renderDropdown(
                                container, 
                                action.name, 
                                actionOptions, 
                                currentVal, 
                                (val) => {
                                    if (val === 'inherit') {
                                        delete state.actionProviders[action.name];
                                    } else {
                                        state.actionProviders[action.name] = val;
                                    }
                                    updateState();
                                }
                            );
                        });
                    }

                    function renderDropdown(container, labelText, options, currentValue, onSelect) {
                        // Check if already open
                        const wasOpen = container.querySelector('.dropdown-content')?.classList.contains('show');

                        let displayLabel = '';
                        const match = options.find(o => o.value === currentValue);
                        displayLabel = match ? match.label : currentValue;

                        let html = \`
                        <div class="filter-row">
                            <div class="filter-label" title="\${labelText}">\${labelText}</div>
                            <div class="dropdown-container">
                                <div class="dropdown-trigger">\${displayLabel}</div>
                                <div class="dropdown-content \${wasOpen ? 'show' : ''}">
                        \`;

                        options.forEach(opt => {
                            const isChecked = opt.value === currentValue;
                            html += \`
                                <div class="dropdown-item \${isChecked ? 'checked' : ''}" data-val="\${opt.value}">
                                    <span class="check">\${isChecked ? '✓' : ''}</span>
                                    <span>\${opt.label}</span>
                                </div>
                            \`;
                        });

                        html += \`
                                </div>
                            </div>
                        </div>
                        \`;

                        container.innerHTML = html;

                        const trigger = container.querySelector('.dropdown-trigger');
                        const content = container.querySelector('.dropdown-content');

                        trigger.onclick = (e) => {
                            e.stopPropagation();
                            // Close others
                            document.querySelectorAll('.dropdown-content').forEach(d => {
                                if (d !== content) d.classList.remove('show');
                            });
                            content.classList.toggle('show');
                        };

                        container.querySelectorAll('.dropdown-item').forEach(item => {
                            item.onclick = (e) => {
                                e.stopPropagation();
                                const val = item.getAttribute('data-val');
                                onSelect(val);
                                content.classList.remove('show');
                            };
                        });
                    }

                    function updateState() {
                        vscode.postMessage({
                            type: 'updateState',
                            value: state
                        });
                    }

                    vscode.postMessage({ type: 'webviewReady' });
                </script>
			</body>
			</html>`;
  }
}

function getNonce() {
  let text = "";
  const possible =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  for (let i = 0; i < 32; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}
