import * as vscode from "vscode";

export interface ProviderState {
  available: boolean;
  path?: string;
  error?: string;
  latency_ms?: number;
}

export interface AgentState {
  last_checked: string;
  providers: { [name: string]: ProviderState };
}

export class AgentStateService {
  private state: AgentState | undefined;

  private _onDidChangeState = new vscode.EventEmitter<AgentState>();
  public readonly onDidChangeState = this._onDidChangeState.event;

  constructor(
    _context: vscode.ExtensionContext,
    private runMonoco: (args: string[], cwd?: string) => Promise<string>,
  ) {
    this.refresh();
  }

  public async refresh() {
    try {
      // Use CLI to get status
      const output = await this.runMonoco(["agent", "status", "--json"]);
      try {
        this.state = JSON.parse(output);
        this.updateContextKeys();
        if (this.state) {
          this._onDidChangeState.fire(this.state);
        }
        console.log("Agent state refreshed:", this.state);
      } catch (e) {
        console.error("Failed to parse agent status JSON", e);
      }
    } catch (e) {
      console.error("Failed to refresh agent state via CLI", e);
    }
  }

  private updateContextKeys() {
    const anyAvailable = Object.values(this.state?.providers || {}).some(
      (p) => p.available,
    );
    vscode.commands.executeCommand(
      "setContext",
      "monoco:agentAvailable",
      anyAvailable,
    );

    if (this.state?.providers) {
      for (const [key, value] of Object.entries(this.state.providers)) {
        vscode.commands.executeCommand(
          "setContext",
          `monoco:${key}Available`,
          value.available,
        );
      }
    }
  }

  public isAvailable(provider: string): boolean {
    return this.state?.providers[provider]?.available ?? false;
  }

  public checkAndShowToast(provider?: string) {
    const available = provider
      ? this.isAvailable(provider)
      : Object.values(this.state?.providers || {}).some((p) => p.available);
    if (!available) {
      vscode.window
        .showWarningMessage(
          "Agent Environment not ready. Please run 'Refine Agent State' or check 'monoco doctor'.",
          "Check Status",
        )
        .then((sel) => {
          if (sel === "Check Status") {
            this.refresh();
          }
        });
    }
  }

  public getAvailableProviders(): string[] {
    if (!this.state?.providers) return [];
    return Object.entries(this.state.providers)
      .filter(([_, value]) => value.available)
      .map(([key]) => key);
  }

  public getState(): AgentState | undefined {
    return this.state;
  }
}
