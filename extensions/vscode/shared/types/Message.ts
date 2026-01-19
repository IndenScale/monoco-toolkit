/**
 * Message types for webview <-> extension communication
 */

import { IssueIndex, IssueMetadata, CreateIssueRequest } from "./Issue";
import { Project } from "./Project";

/**
 * Messages sent from webview to extension
 */
export type WebviewMessage =
  | { type: "GET_LOCAL_DATA" }
  | { type: "SAVE_STATE"; key: string; value: any }
  | { type: "UPDATE_ISSUE"; issueId: string; changes: Partial<IssueMetadata> }
  | { type: "CREATE_ISSUE"; value: CreateIssueRequest }
  | { type: "OPEN_ISSUE_FILE"; value: { path: string } }
  | {
      type: "OPEN_FILE";
      path?: string;
      line?: number;
      column?: number;
      value?: { path?: string; line?: number; column?: number };
    }
  | { type: "OPEN_URL"; url: string }
  | { type: "UPDATE_CONFIG"; value: { key: string; value: string } };

/**
 * Messages sent from extension to webview
 */
export type ExtensionMessage =
  | {
      type: "DATA_UPDATED";
      payload: {
        issues: IssueIndex[];
        projects: Project[];
        workspaceState?: {
          last_active_project_id?: string | null;
        };
      };
    }
  | { type: "REFRESH" }
  | { type: "SHOW_CREATE_VIEW"; value?: { type?: string; parent?: string } }
  | { type: "SHOW_SETTINGS" }
  | { type: "AGENT_STATE_UPDATED"; payload: { providers: string[] } };

/**
 * Type guard for webview messages
 */
export function isWebviewMessage(message: any): message is WebviewMessage {
  return message && typeof message.type === "string";
}

/**
 * Type guard for extension messages
 */
export function isExtensionMessage(message: any): message is ExtensionMessage {
  return message && typeof message.type === "string";
}
