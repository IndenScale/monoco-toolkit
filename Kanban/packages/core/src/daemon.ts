import { create } from "zustand";
import { DaemonInfo, DaemonStatus, Project } from "./types";

const DEFAULT_DAEMON_URL =
  typeof window !== "undefined"
    ? window.localStorage?.getItem("monoco_daemon_url") ||
      "http://127.0.0.1:8642"
    : "http://127.0.0.1:8642";

export class DaemonClient {
  static async checkHealth(url: string): Promise<boolean> {
    try {
      const res = await fetch(`${url}/health`);
      return res.ok;
    } catch {
      return false;
    }
  }

  static async getInfo(url: string, projectId?: string): Promise<DaemonInfo> {
    const params = projectId ? `?project_id=${projectId}` : '';
    const res = await fetch(`${url}/api/v1/info${params}`);
    if (!res.ok) throw new Error("Failed to fetch info");
    return res.json();
  }

  static async getProjects(url: string): Promise<Project[]> {
    const res = await fetch(`${url}/api/v1/projects`);
    if (!res.ok) throw new Error("Failed to fetch projects");
    return res.json();
  }
}

interface DaemonState {
  status: DaemonStatus;
  info: DaemonInfo | null;
  projects: Project[];
  currentProjectId: string | null;
  lastChecked: number;
  daemonUrl: string;
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
  setStatus: (status) => set({ status }),
  setInfo: (info) => set({ info }),
  setProjects: (projects) => set({ projects }),
  setCurrentProjectId: (id) => {
      set({ currentProjectId: id });
      // When project changes, refresh info
      get().checkConnection();
  },
  setDaemonUrl: (url) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("monoco_daemon_url", url);
    }
    // Force UI update and reset state for new URL
    set({ daemonUrl: url, status: "connecting", info: null, projects: [], currentProjectId: null });
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
        // Fetch projects first
        const projects = await DaemonClient.getProjects(daemonUrl);
        set({ projects });
        
        let targetProjectId = currentProjectId;
        if (!targetProjectId && projects.length > 0) {
            targetProjectId = projects[0].id;
            set({ currentProjectId: targetProjectId });
        }

        const info = await DaemonClient.getInfo(daemonUrl, targetProjectId || undefined);
        set({ status: "connected", info });
      } else {
        set({ status: "error" });
      }
    } catch (error) {
      console.error("Daemon connection failed:", error);
      set({ status: "error" });
    }
  },
}));

import { useEffect, useRef } from "react";

export function useDaemonLifecycle(
  baseIntervalMs = 15000,
  maxIntervalMs = 30000
) {
  const { checkConnection, status } = useDaemonStore();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const intervalRef = useRef(baseIntervalMs);

  useEffect(() => {
    const scheduleNextCheck = () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);

      timeoutRef.current = setTimeout(async () => {
        await checkConnection();

        // Determine next interval based on result
        const currentStatus = useDaemonStore.getState().status;

        if (currentStatus === "connected") {
          // Reset to fast polling when connected
          intervalRef.current = baseIntervalMs;
        } else {
          // Exponential backoff when disconnected/error
          intervalRef.current = Math.min(
            intervalRef.current * 1.5,
            maxIntervalMs
          );
          console.log(
            `Daemon offline. Retrying in ${Math.round(
              intervalRef.current / 1000
            )}s...`
          );
        }

        scheduleNextCheck();
      }, intervalRef.current);
    };

    // Initial check immediately
    checkConnection().then(() => {
      // Start the loop
      scheduleNextCheck();
    });

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [checkConnection, baseIntervalMs, maxIntervalMs]);

  return status;
}
