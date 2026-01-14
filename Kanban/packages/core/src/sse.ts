import { useEffect } from "react";
import { useDaemonStore } from "./daemon";

type EventCallback = (data: any) => void;

class SSEManager {
  private eventSource: EventSource | null = null;
  private listeners: Map<string, Set<EventCallback>> = new Map();
  private currentUrl: string | null = null;

  connect(baseUrl: string) {
    const targetUrl = `${baseUrl}/api/v1/events`;

    if (
      this.currentUrl === targetUrl &&
      this.eventSource &&
      (this.eventSource.readyState === EventSource.OPEN ||
        this.eventSource.readyState === EventSource.CONNECTING)
    ) {
      return;
    }

    this.disconnect();

    console.log(`[SSE] Connecting to ${targetUrl}`);
    this.currentUrl = targetUrl;
    this.eventSource = new EventSource(targetUrl);

    this.eventSource.onopen = () => {
      console.log("[SSE] Connected");
    };

    // Listen for generic messages if any
    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // If data has a 'type' field, treat it as a specific event
        const eventType = data.type || "message";
        this.emit(eventType, data.payload || data);
      } catch (e) {
        console.warn("[SSE] Failed to parse generic message", event.data);
      }
    };

    // Listen for specific issue events (Assuming server sends name: event lines)
    // We bind generic handlers that parse the data and emit internally
    const bindEvent = (eventName: string) => {
      this.eventSource?.addEventListener(eventName, (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          this.emit(eventName, data);
        } catch (err) {
          console.error(`[SSE] Error parsing ${eventName}`, err);
        }
      });
    };

    bindEvent("issue_upserted");
    bindEvent("issue_deleted");
    bindEvent("project_created");
    bindEvent("project_updated");
    bindEvent("project_deleted");

    this.eventSource.onerror = (err) => {
      console.error("[SSE] Connection error", err);
      // EventSource will retry automatically, but we can potentially notify the store
    };
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this.currentUrl = null;
    }
  }

  on(event: string, callback: EventCallback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
    return () => this.off(event, callback);
  }

  off(event: string, callback: EventCallback) {
    this.listeners.get(event)?.delete(callback);
  }

  private emit(event: string, data: any) {
    if (event === "issue_upserted") {
      this.bufferIssueUpdate(data);
      return;
    }
    this.listeners.get(event)?.forEach((cb) => cb(data));
  }

  private issueBuffer: Map<string, any> = new Map();
  private batchTimer: ReturnType<typeof setTimeout> | null = null;

  private bufferIssueUpdate(data: any) {
    const id = data.id;
    if (id) {
      // Deduplicate: latest update wins
      this.issueBuffer.set(id, data);
    }

    if (!this.batchTimer) {
      this.batchTimer = setTimeout(() => {
        const batch = Array.from(this.issueBuffer.values());
        this.issueBuffer.clear();
        this.batchTimer = null;
        this.listeners.get("issues_batch_upserted")?.forEach((cb) => cb(batch));
      }, 100); // 100ms batch window
    }
  }
}

export const sseManager = new SSEManager();

/**
 * Hook to automatically connect/disconnect based on daemon status
 */
export function useSSEConnection() {
  const { status, daemonUrl } = useDaemonStore();

  useEffect(() => {
    if (status === "connected") {
      sseManager.connect(daemonUrl);
    } else {
      sseManager.disconnect();
    }
  }, [status, daemonUrl]);
}
