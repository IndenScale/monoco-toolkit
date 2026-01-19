import * as vscode from "vscode";

export interface FilterState {
  project: string | null;
  types: string[];
  statuses: string[];
  stages: string[];
  tagQuery: string;
}

export class IssueFilterWebviewProvider implements vscode.WebviewViewProvider {
  private _view?: vscode.WebviewView;
  private projects: string[] = [];

  // Default State
  private state: FilterState = {
    project: null,
    types: [],
    statuses: [],
    stages: [],
    tagQuery: "",
  };

  private _onDidUpdateFilter = new vscode.EventEmitter<FilterState>();
  readonly onDidUpdateFilter = this._onDidUpdateFilter.event;

  constructor(private readonly _extensionUri: vscode.Uri) {}

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
        case "updateFilter":
          this.state = data.value;
          this._onDidUpdateFilter.fire(this.state);
          break;
        case "webviewReady":
          this.updateWebview();
          break;
      }
    });
  }

  public setProjects(projects: string[]) {
    this.projects = projects;
    this.updateWebview();
  }

  private updateWebview() {
    if (this._view) {
      this._view.webview.postMessage({
        type: "initState",
        projects: this.projects,
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
				<title>Filters</title>
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
                        justify-content: flex-end;
                    }

                    .main-container {
                        padding: 10px 10px 15px 10px;
                        display: flex;
                        flex-direction: column;
                        gap: 12px;
                        /* max-height: 100vh; Removed to allow scroll */
                    }

                    /* Filters Section */
                    .filters-container {
                        display: flex;
                        flex-direction: column;
                        gap: 8px;
                    }

                    .filter-row {
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        gap: 10px;
                    }

                    .filter-label {
                        font-size: 11px;
                        font-weight: 600;
                        text-transform: uppercase;
                        opacity: 0.8;
                        min-width: 60px;
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
                        padding: 3px 8px; /* Slightly tighter */
                        border-radius: 2px;
                        cursor: pointer;
                        font-size: 12px;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        height: 22px; /* Fixed height for consistency */
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
                        bottom: 100%; /* Open Upwards */
                        left: 0;
                        right: 0;
                        background: var(--dropdown-bg);
                        border: 1px solid var(--focus-border);
                        z-index: 100;
                        max-height: 200px;
                        overflow-y: auto;
                        box-shadow: 0 -4px 6px rgba(0,0,0,0.2); /* Shadow up */
                        margin-bottom: 2px;
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

                    .dropdown-item.checked {
                        /* font-weight: bold; */
                    }

                    .dropdown-item .check {
                        opacity: 0;
                        width: 14px;
                    }
                    .dropdown-item.checked .check {
                        opacity: 1;
                    }

                    /* Search Section (Bottom) */
                    .search-container {
                        /* No margin-top auto, effectively attaches to filters */
                        padding-top: 4px;
                        /* border-top: 1px solid var(--vscode-widget-border); REMOVED border for integration */
                    }

                    input[type="text"] {
                        background: var(--input-bg);
                        color: var(--input-fg);
                        border: 1px solid var(--input-border);
                        padding: 4px 6px;
                        width: 100%;
                        box-sizing: border-box;
                        border-radius: 2px;
                        outline: none;
                        font-family: inherit;
                        font-size: 12px;
                        height: 24px;
                    }
                    input[type="text"]:focus {
                        border-color: var(--focus-border);
                    }
                    .help-text {
                        font-size: 10px;
                        opacity: 0.6;
                        margin-top: 4px;
                        margin-left: 2px;
                    }

                    /* Scrollbar */
                    ::-webkit-scrollbar { width: 6px; }
                    ::-webkit-scrollbar-track { background: transparent; }
                    ::-webkit-scrollbar-thumb { background: var(--vscode-scrollbarSlider-background); border-radius: 3px; }
                </style>
			</head>
			<body>
                <div class="main-container">
                    <!-- Filters (Top) -->
                    <div class="filters-container">
                        <div id="project-filter"></div>
                        <div id="type-filter"></div>
                        <div id="status-filter"></div>
                        <div id="stage-filter"></div>
                    </div>

                    <!-- Search (Bottom) -->
                    <div class="search-container">
                        <input type="text" id="tag-input" placeholder="Search / Tags...">
                        <div class="help-text">+must -exclude #nice-to-have</div>
                    </div>
                </div>

				<script nonce="${nonce}">
                    const vscode = acquireVsCodeApi();

                    // State
                    let state = {
                        project: null,
                        types: [],
                        statuses: [],
                        stages: [],
                        tagQuery: ""
                    };
                    let projects = [];

                    // Config
                    const TYPES = ['epic', 'arch', 'feature', 'chore', 'fix', 'bug'];
                    const STATUSES = ['open', 'backlog', 'closed'];
                    const STAGES = ['draft', 'doing', 'review', 'done'];

                    // Elements
                    const els = {
                        project: document.getElementById('project-filter'),
                        type: document.getElementById('type-filter'),
                        status: document.getElementById('status-filter'),
                        stage: document.getElementById('stage-filter'),
                        tag: document.getElementById('tag-input')
                    };

                    // Init
                    window.addEventListener('message', event => {
                        const message = event.data;
                        switch (message.type) {
                            case 'initState':
                                projects = message.projects || [];
                                state = message.state || state;
                                renderAll();
                                break;
                        }
                    });

                    // Search Input
                    els.tag.addEventListener('input', (e) => {
                        state.tagQuery = e.target.value;
                        emitState();
                    });

                    // Close dropdowns on outside click
                    document.addEventListener('click', (e) => {
                        if (!e.target.closest('.dropdown-container')) {
                            document.querySelectorAll('.dropdown-content').forEach(d => d.classList.remove('show'));
                        }
                    });

                    function renderAll() {
                        // Projects
                        let projectOpts = [
                           { label: 'All Projects', value: 'all', isDefault: true },
                           { label: 'Root Only', value: 'root' },
                           ...projects.map(p => ({ label: p, value: p }))
                        ];
                        // Convert project 'null' state to 'all' value for UI
                        let currentProj = state.project === null ? 'all' : state.project;

                        renderDropdown(els.project, 'Project', projectOpts, [currentProj], true, (val) => {
                             state.project = val === 'all' ? null : val;
                             emitState();
                             // Project is single select, so we re-render to update trigger text immediately
                             renderAll();
                        });

                        // Types
                        renderDropdown(els.type, 'Type', TYPES.map(t => ({label: t, value: t})), state.types, false, (val) => {
                            toggleArray(state.types, val);
                            emitState();
                            renderAll();
                        });

                        // Statuses
                        renderDropdown(els.status, 'Status', STATUSES.map(s => ({label: s, value: s})), state.statuses, false, (val) => {
                            toggleArray(state.statuses, val);
                            emitState();
                            renderAll();
                        });

                        // Stages
                        renderDropdown(els.stage, 'Stage', STAGES.map(s => ({label: s, value: s})), state.stages, false, (val) => {
                            toggleArray(state.stages, val);
                            emitState();
                            renderAll();
                        });

                        // Tag Input
                        els.tag.value = state.tagQuery;
                    }

                    function renderDropdown(container, labelText, options, currentValues, isSingle, onSelect) {
                        // Only create structure if empty (to avoid losing open state if possible, though re-render might close it)
                        // For simplicity in this version, we reconstruct content but keep open state if matches

                        // Check if already open
                        const wasOpen = container.querySelector('.dropdown-content')?.classList.contains('show');

                        let displayValue = '';
                         if (currentValues.length === 0 || (currentValues.length === 1 && currentValues[0] === 'all')) {
                            displayValue = 'All';
                        } else if (currentValues.length === options.length && !isSingle) {
                             displayValue = 'All';
                        } else if (isSingle) {
                             const match = options.find(o => o.value === currentValues[0]);
                             displayValue = match ? match.label : currentValues[0];
                        } else {
                            if (currentValues.length > 2) {
                                displayValue = \`\${currentValues.length} Selected\`;
                            } else {
                                displayValue = currentValues.join(', ');
                            }
                        }

                        let html = \`
                        <div class="filter-row">
                            <div class="filter-label">\${labelText}</div>
                            <div class="dropdown-container">
                                <div class="dropdown-trigger">\${displayValue}</div>
                                <div class="dropdown-content \${wasOpen ? 'show' : ''}">
                        \`;

                        options.forEach(opt => {
                            const isChecked = currentValues.includes(opt.value);
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
                                if (isSingle) {
                                    content.classList.remove('show');
                                }
                            };
                        });
                    }

                    function toggleArray(arr, val) {
                        const idx = arr.indexOf(val);
                        if (idx > -1) arr.splice(idx, 1);
                        else arr.push(val);
                    }

                    function emitState() {
                        vscode.postMessage({
                            type: 'updateFilter',
                            value: state
                        });
                    }

                    // Signal Ready
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
