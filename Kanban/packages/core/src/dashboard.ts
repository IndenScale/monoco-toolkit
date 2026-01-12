import { create } from "zustand";
import { DashboardStats } from "./types";
import { useDaemonStore } from "./daemon";

interface DashboardState {
  stats: DashboardStats | null;
  isLoading: boolean;
  fetchStats: () => Promise<void>;
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  stats: null,
  isLoading: false,

  fetchStats: async () => {
    // @ts-ignore
    const { daemonUrl, status, currentProjectId } = useDaemonStore.getState();
    if (status !== "connected") return;

    set({ isLoading: true });
    try {
      const params = currentProjectId ? `?project_id=${currentProjectId}` : '';
      const res = await fetch(`${daemonUrl}/api/v1/stats/dashboard${params}`);
      if (res.ok) {
        const stats: DashboardStats = await res.json();
        set({ stats, isLoading: false });
      } else {
        console.error("Failed to fetch dashboard stats", res.status);
        set({ isLoading: false });
      }
    } catch (e) {
      console.error("Failed to fetch dashboard stats", e);
      set({ isLoading: false });
    }
  },
}));
