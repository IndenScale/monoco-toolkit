import { create } from "zustand";
import { DaemonInfo, DaemonStatus, Project } from "./types";

const DEFAULT_DAEMON_URL =
  typeof window !== "undefined"
    ? window.localStorage?.getItem("monoco_daemon_url") ||
      process.env.NEXT_PUBLIC_MONOCO_DAEMON_URL ||
      "http://127.0.0.1:8642"
    : process.env.NEXT_PUBLIC_MONOCO_DAEMON_URL || "http://127.0.0.1:8642";

// Helper for fetch with timeout
async function fetchWithTimeout(
  resource: RequestInfo,
  options: RequestInit & { timeout?: number } = {}
) {
  const { timeout = 2000, ...rest } = options;

  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(resource, {
      ...rest,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(id);
  }
}

export class DaemonClient {
  static async checkHealth(url: string): Promise<boolean> {
    try {
      const res = await fetchWithTimeout(`${url}/health`, {
        cache: "no-store",
        timeout: 5000,
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  static async getInfo(url: string, projectId?: string): Promise<DaemonInfo> {
    const params = projectId ? `?project_id=${projectId}` : "";
    const res = await fetchWithTimeout(`${url}/api/v1/info${params}`, {
      cache: "no-store",
      timeout: 5000,
    });
    if (!res.ok) throw new Error("Failed to fetch info");
    return res.json();
  }

  static async getProjects(url: string): Promise<Project[]> {
    const res = await fetchWithTimeout(`${url}/api/v1/projects`, {
      cache: "no-store",
      timeout: 5000,
    });
    if (!res.ok) throw new Error("Failed to fetch projects");
    return res.json();
  }

  static async getWorkspaceState(url: string): Promise<any> {
    try {
      const res = await fetchWithTimeout(`${url}/api/v1/workspace/state`, {
        cache: "no-store",
        timeout: 5000,
      });
      if (res.ok) return res.json();
    } catch (e) {
      console.warn("Failed to fetch workspace state", e);
    }
    return {};
  }

  static async setWorkspaceState(url: string, state: any): Promise<void> {
    try {
      await fetchWithTimeout(`${url}/api/v1/workspace/state`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state),
        timeout: 5000,
      });
    } catch (e) {
      console.warn("Failed to set workspace state", e);
    }
  }
}

interface DaemonState {
  status: DaemonStatus;
  info: DaemonInfo | null;
  projects: Project[];
  currentProjectId: string | null;
  lastChecked: number;
  daemonUrl: string;
  errorCount: number;
  setStatus: (status: DaemonStatus) => void;
  setInfo: (info: DaemonInfo) => void;
  setProjects: (projects: Project[]) => void;
  setCurrentProjectId: (id: string | null) => void;
  setDaemonUrl: (url: string) => void;
  checkConnection: () => Promise<void>;
  refreshProjects: () => Promise<void>;
}

export const useDaemonStore = create<DaemonState>((set, get) => ({
  status: "disconnected",
  info: null,
  projects: [],
  currentProjectId: null,
  lastChecked: 0,
  daemonUrl: DEFAULT_DAEMON_URL,
  errorCount: 0,
  setStatus: (status) => set({ status }),
  setInfo: (info) => set({ info }),
  setProjects: (projects) => set({ projects }),
  setCurrentProjectId: (id) => {
    set({ currentProjectId: id });
    // Persist state when checking project
    if (id) {
      DaemonClient.setWorkspaceState(get().daemonUrl, {
        last_active_project_id: id,
      });
    }
    // When project changes, refresh info
    get().checkConnection();
  },
  setDaemonUrl: (url) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("monoco_daemon_url", url);
    }
    // Force UI update and reset state for new URL
    set({
      daemonUrl: url,
      status: "connecting",
      info: null,
      projects: [],
      currentProjectId: null,
    });
    get().checkConnection();
  },
  refreshProjects: async () => {
    const { daemonUrl } = get();
    try {
      const projects = await DaemonClient.getProjects(daemonUrl);
      set({ projects });

      // Auto-select first project if none selected
      const { currentProjectId } = get();
      if (!currentProjectId && projects.length > 0) {
        set({ currentProjectId: projects[0].id });
      }
    } catch (e) {
      console.error("Failed to refresh projects", e);
    }
  },
  checkConnection: async () => {
    // If already connected or connecting, skip simple health checks
    // This logic might need refinement for actual polling vs reconnection
    set({ lastChecked: Date.now() });
    const { daemonUrl, currentProjectId } = get();
    try {
      // Only set connecting if we are in a state that needs feedback
      // We don't want to flash 'connecting' on every poll if we are already connected
      if (get().status === "disconnected" || get().status === "error") {
        set({ status: "connecting" });
      }

      const isHealthy = await DaemonClient.checkHealth(daemonUrl);

      if (isHealthy) {
        set({ errorCount: 0 });
        // Fetch projects first
        const projects = await DaemonClient.getProjects(daemonUrl);
        set({ projects });

        let targetProjectId = currentProjectId;

        // If no project selected (e.g. initial load), try to restore from server state
        if (!targetProjectId) {
          const state = await DaemonClient.getWorkspaceState(daemonUrl);
          if (state.last_active_project_id) {
            // Validate existence in current project list
            if (
              projects.some(
                (p: Project) => p.id === state.last_active_project_id
              )
            ) {
              targetProjectId = state.last_active_project_id;
            }
          }

          // Fallback to first project if still null
          if (!targetProjectId && projects.length > 0) {
            targetProjectId = projects[0].id;
          }

          if (targetProjectId) {
            set({ currentProjectId: targetProjectId });
          }
        }

        if (targetProjectId) {
          const info = await DaemonClient.getInfo(daemonUrl, targetProjectId);
          set({ status: "connected", info });
        } else {
          set({ status: "connected", info: null });
        }
      } else {
        const { errorCount, status } = get();
        const newErrorCount = errorCount + 1;
        set({ errorCount: newErrorCount });

        if (status === "connected" && newErrorCount < 3) {
          // Keep connection alive for minor glitches
          return;
        }
        set({ status: "error" });
      }
    } catch (error: any) {
      // Enhanced logging to debug "permanent offline" issues
      if (error.name === "AbortError") {
        console.warn(`[Daemon] Connection timed out after 5000ms`);
      } else {
        console.error("[Daemon] Connection failed:", error);
      }

      const { errorCount, status } = get();
      const newErrorCount = errorCount + 1;
      set({ errorCount: newErrorCount });

      if (status === "connected" && newErrorCount < 3) {
        return;
      }
      set({ status: "error" });
    }
  },
}));

import { useEffect, useRef } from "react";

export function useDaemonLifecycle(
  baseIntervalMs = 5000,
  maxIntervalMs = 10000
) {
  const status = useDaemonStore((s) => s.status);
  const daemonUrl = useDaemonStore((s) => s.daemonUrl);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  // Start with a short interval for quick feedback on load
  const intervalRef = useRef(1000);
  const isMountedRef = useRef(true);

  // Hydrate URL from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedUrl = window.localStorage.getItem("monoco_daemon_url");
      const currentUrl = useDaemonStore.getState().daemonUrl;
      // If we have a stored URL that differs from default/current, use it
      if (storedUrl && storedUrl !== currentUrl) {
        useDaemonStore.getState().setDaemonUrl(storedUrl);
      }
    }
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    const checkConnection = useDaemonStore.getState().checkConnection;

    // Reset interval on url change
    intervalRef.current = 1000;

    const scheduleNextCheck = () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);

      timeoutRef.current = setTimeout(async () => {
        if (!isMountedRef.current) return;

        await checkConnection();

        if (!isMountedRef.current) return;

        // Determine next interval based on result
        const currentStatus = useDaemonStore.getState().status;

        if (currentStatus === "connected") {
          // Reset to slow polling when connected
          intervalRef.current = baseIntervalMs;
        } else {
          // Exponential backoff when disconnected/error, but start from current interval
          // Start fast (1s) -> 1.5s -> 2.25s -> ... -> max (10s)
          intervalRef.current = Math.min(
            intervalRef.current * 1.5,
            maxIntervalMs
          );
        }

        scheduleNextCheck();
      }, intervalRef.current);
    };

    // Initial check immediately
    checkConnection().then(() => {
      if (isMountedRef.current) {
        scheduleNextCheck();
      }
    });

    return () => {
      isMountedRef.current = false;
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [baseIntervalMs, maxIntervalMs, daemonUrl]);

  return status;
}
