import { create } from "zustand";
import { useEffect } from "react";
import { Issue } from "./types";
import { useDaemonStore } from "./daemon";
import { sseManager } from "./sse";
import { useDashboardStore } from "./dashboard";

interface KanbanState {
  issues: Issue[];
  isLoading: boolean;
  filter: string;
  fetchIssues: () => Promise<void>;
  setFilter: (filter: string) => void;
  upsertIssue: (issue: Issue) => void;
  batchUpsertIssues: (newIssues: Issue[]) => void;
  removeIssue: (issueId: string) => void;
}

export const useKanbanStore = create<KanbanState>((set, get) => ({
  issues: [],
  isLoading: false,
  filter: "",

  fetchIssues: async () => {
    // @ts-ignore - core types might be lagging
    const { daemonUrl, status, currentProjectId } = useDaemonStore.getState();
    if (status !== "connected") return;

    set({ isLoading: true });
    try {
      const params = currentProjectId ? `?project_id=${currentProjectId}` : "";
      const res = await fetch(`${daemonUrl}/api/v1/issues${params}`, {
        cache: "no-store",
      });
      if (res.ok) {
        const issues: Issue[] = await res.json();
        set({ issues, isLoading: false });
      } else {
        console.error("Failed to fetch issues: Status", res.status);
        set({ isLoading: false });
      }
    } catch (e) {
      console.error("Failed to fetch issues", e);
      set({ isLoading: false });
    }
  },

  setFilter: (filter: string) => set({ filter }),

  upsertIssue: (issue: Issue) => {
    const { issues } = get();
    const index = issues.findIndex((t) => t.id === issue.id);
    if (index >= 0) {
      const newIssues = [...issues];
      newIssues[index] = issue;
      set({ issues: newIssues });
    } else {
      set({ issues: [...issues, issue] });
    }
  },

  batchUpsertIssues: (newItems: Issue[]) => {
    const { issues } = get();
    const issuesCopy = [...issues];
    let changed = false;

    newItems.forEach((item) => {
      const index = issuesCopy.findIndex((t) => t.id === item.id);
      if (index >= 0) {
        issuesCopy[index] = item;
        changed = true;
      } else {
        issuesCopy.push(item);
        changed = true;
      }
    });

    if (changed) {
      set({ issues: issuesCopy });
    }
  },

  removeIssue: (issueId: string) => {
    set({ issues: get().issues.filter((t) => t.id !== issueId) });
  },
}));

export function useKanbanSync() {
  // @ts-ignore
  const { status, currentProjectId } = useDaemonStore();
  const { fetchIssues, upsertIssue, batchUpsertIssues, removeIssue } =
    useKanbanStore();
  const { fetchStats } = useDashboardStore();

  // Initial fetch on connection or project change
  useEffect(() => {
    if (status === "connected") {
      fetchIssues();
      fetchStats();
    }
  }, [status, currentProjectId, fetchIssues, fetchStats]);

  // SSE Event binding
  useEffect(() => {
    const onBatchUpsert = (items: any[]) => {
      // Filter by project_id if available
      const filtered = items.filter((data) => {
        if (
          data.project_id &&
          currentProjectId &&
          data.project_id !== currentProjectId
        ) {
          return false;
        }
        return true;
      });

      if (filtered.length > 0) {
        batchUpsertIssues(filtered);
        fetchStats();
      }
    };
    const onDelete = (data: any) => {
      // Handle if data is just ID or object with ID
      const id = typeof data === "string" ? data : data.id;
      // Filter by project_id if available (assuming data might be an object now)
      if (
        typeof data === "object" &&
        data.project_id &&
        currentProjectId &&
        data.project_id !== currentProjectId
      ) {
        return;
      }
      if (id) removeIssue(id);
      fetchStats();
    };

    const onProjectChange = () => {
      useDaemonStore.getState().refreshProjects();
    };

    const unsubUpsert = sseManager.on("issues_batch_upserted", onBatchUpsert);
    const unsubDelete = sseManager.on("issue_deleted", onDelete);
    const unsubPrjCreate = sseManager.on("project_created", onProjectChange);
    const unsubPrjUpdate = sseManager.on("project_updated", onProjectChange);
    const unsubPrjDelete = sseManager.on("project_deleted", onProjectChange);

    return () => {
      unsubUpsert();
      unsubDelete();
      unsubPrjCreate();
      unsubPrjUpdate();
      unsubPrjDelete();
    };
  }, [batchUpsertIssues, removeIssue, fetchStats, currentProjectId]);
}

export * from "./types";
export * from "./daemon";
export * from "./sse";
export * from "./dashboard";
export * from "./bridge";
