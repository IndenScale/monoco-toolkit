import { StateManager } from "../state/StateManager";
import { IssueMetadata } from "@shared/types/Issue";

/**
 * Message types sent from webview to extension
 */
export type WebviewMessage =
  | { type: "GET_LOCAL_DATA" }
  | { type: "SAVE_STATE"; key: string; value: any }
  | { type: "UPDATE_ISSUE"; issueId: string; changes: Partial<IssueMetadata> }
  | {
      type: "CREATE_ISSUE";
      value: { title: string; type: string; parent?: string };
    }
  | { type: "OPEN_ISSUE_FILE"; value: { path: string } }
  | { type: "UPDATE_CONFIG"; value: { key: string; value: string } }
  | { type: "PERFORM_ACTION"; issueId: string; action: string };

/**
 * Message types received from extension
 */
export type ExtensionMessage =
  | {
      type: "DATA_UPDATED";
      payload: {
        issues: any[];
        projects: any[];
        workspaceState?: { last_active_project_id?: string };
      };
    }
  | { type: "REFRESH" }
  | { type: "SHOW_CREATE_VIEW"; value?: { type: string; parent?: string } };

/**
 * VSCode API bridge for webview communication
 * Handles all message passing between webview and extension
 */
export class VSCodeBridge {
  private vscode: any;
  private handlers = new Map<string, (payload: any) => void>();

  constructor(private stateManager: StateManager) {
    // Acquire VSCode API
    this.vscode = (window as any).acquireVsCodeApi();

    // Setup message listener
    window.addEventListener("message", (event) => {
      const message = event.data as ExtensionMessage;
      console.log("[VSCodeBridge] Received message:", message.type, message);
      const handler = this.handlers.get(message.type);
      if (handler) {
        handler((message as any).payload || (message as any).value);
      } else {
        console.warn(
          "[VSCodeBridge] No handler for message type:",
          message.type,
        );
      }
    });
  }

  /**
   * Register a message handler
   */
  on(type: string, handler: (payload: any) => void) {
    this.handlers.set(type, handler);
  }

  /**
   * Send a message to the extension
   */
  send(message: WebviewMessage) {
    console.log("[VSCodeBridge] Sending message:", message.type, message);
    this.vscode.postMessage(message);
  }

  /**
   * Request local data from extension
   */
  getLocalData() {
    console.log("[VSCodeBridge] Requesting local data...");
    this.send({ type: "GET_LOCAL_DATA" });
  }

  /**
   * Save state to extension
   */
  saveState(key: string, value: any) {
    this.send({ type: "SAVE_STATE", key, value });
  }

  /**
   * Update an issue
   */
  updateIssue(issueId: string, changes: Partial<IssueMetadata>) {
    this.send({ type: "UPDATE_ISSUE", issueId, changes });
  }

  /**
   * Create a new issue
   */
  createIssue(value: { title: string; type: string; parent?: string }) {
    this.send({ type: "CREATE_ISSUE", value });
  }

  /**
   * Open an issue file in editor
   */
  openIssueFile(path: string) {
    this.send({ type: "OPEN_ISSUE_FILE", value: { path } });
  }

  /**
   * Perform an action on an issue
   */
  performAction(issueId: string, action: string) {
    this.send({ type: "PERFORM_ACTION", issueId, action });
  }

  /**
   * Save active project selection
   */
  async setActiveProject(projectId: string) {
    this.saveState("last_active_project_id", projectId);
    this.stateManager.updateField("selectedProjectId", projectId);
  }
}
