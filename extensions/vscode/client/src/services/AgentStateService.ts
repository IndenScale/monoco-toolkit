import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

export interface AgentState {
  last_checked: string;
  providers: Record<string, { available: boolean; path?: string }>;
}

export class AgentStateService {
  private state: AgentState | undefined;
  private readonly statePath: string;

  constructor(private context: vscode.ExtensionContext) {
    this.statePath = path.join(os.homedir(), ".monoco", "agent_state.yaml");
    this.initialize();
  }

  private initialize() {
    // Initial read
    this.readState();

    // Watch for changes using fs.watchFile for cross-platform simplicity on external files
    fs.watchFile(this.statePath, (curr, prev) => {
      if (curr.mtime !== prev.mtime) {
        console.log("Agent state file changed, reloading...");
        this.readState();
      }
    });

    // Clean up watcher on extension deactivation
    this.context.subscriptions.push({
      dispose: () => {
        fs.unwatchFile(this.statePath);
      },
    });
  }

  private readState() {
    try {
      if (fs.existsSync(this.statePath)) {
        const content = fs.readFileSync(this.statePath, "utf8");
        this.state = this.parseYaml(content);
        this.updateContextKeys();
        console.log("Agent state loaded:", this.state);
      } else {
        console.log("Agent state file not found:", this.statePath);
        this.state = undefined;
        this.updateContextKeys();
      }
    } catch (e) {
      console.error("Failed to read agent_state.yaml", e);
    }
  }

  private parseYaml(content: string): AgentState {
    // Simple manual parser for specific structure managed by Toolkit
    const result: AgentState = { last_checked: "", providers: {} };
    const lines = content.split("\n");
    let currentProvider: string | null = null;

    // Regex for parsing
    // providers:
    //   gemini:
    //     available: true

    for (const line of lines) {
      // Very simple line-based parsing
      // Use regex to detect indentation and keys

      // last_checked: "..."
      const lastCheckedMatch = line.match(/^last_checked:\s*(.*)/);
      if (lastCheckedMatch) {
        result.last_checked = lastCheckedMatch[1].trim().replace(/^"|"$/g, "");
        continue;
      }

      //   provider_name:
      const providerMatch = line.match(/^  ([\w-]+):\s*$/);
      if (providerMatch) {
        currentProvider = providerMatch[1];
        result.providers[currentProvider] = { available: false };
        continue;
      }

      //     available: true
      const availableMatch = line.match(/^    available:\s*(true|false)/);
      if (availableMatch && currentProvider) {
        result.providers[currentProvider].available =
          availableMatch[1] === "true";
        continue;
      }

      //     path: "..."
      const pathMatch = line.match(/^    path:\s*(.*)/);
      if (pathMatch && currentProvider) {
        result.providers[currentProvider].path = pathMatch[1]
          .trim()
          .replace(/^"|"$/g, "");
        continue;
      }
    }
    return result;
  }

  private updateContextKeys() {
    const anyAvailable = Object.values(this.state?.providers || {}).some(
      (p) => p.available
    );
    vscode.commands.executeCommand(
      "setContext",
      "monoco:agentAvailable",
      anyAvailable
    );

    if (this.state?.providers) {
      for (const [key, value] of Object.entries(this.state.providers)) {
        vscode.commands.executeCommand(
          "setContext",
          `monoco:${key}Available`,
          value.available
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
      vscode.window.showWarningMessage(
        "Agent Environment not ready. Please run 'monoco doctor' in terminal."
      );
    }
  }
}
