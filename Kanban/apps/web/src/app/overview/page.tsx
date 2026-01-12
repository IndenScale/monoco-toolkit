"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import {
  Spinner,
  Intent,
  Callout,
  Button,
  InputGroup,
  Popover,
  Position,
  Menu,
  MenuItem,
} from "@blueprintjs/core";
import {
  useDaemonStore,
  useSSEConnection,
  sseManager,
} from "@monoco/kanban-core";
import KanbanColumn from "../components/KanbanColumn";
import IssueDetailModal from "../components/IssueDetailModal";
import CreateIssueDialog from "../components/CreateIssueDialog";
import { Issue } from "../types";

export default function OverviewPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [focusedIssueId, setFocusedIssueId] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [filterText, setFilterText] = useState("");

  // @ts-ignore - core types might be lagging
  const { daemonUrl, status, currentProjectId } = useDaemonStore();

  // Ensure SSE is active
  useSSEConnection();

  const fetchIssues = useCallback(async () => {
    if (status !== "connected") return;
    try {
      const params = currentProjectId ? `?project_id=${currentProjectId}` : "";
      const res = await fetch(`${daemonUrl}/api/v1/issues${params}`);
      if (!res.ok) throw new Error("Failed to fetch issues");
      const data = await res.json();
      setIssues(data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [daemonUrl, status, currentProjectId]);

  useEffect(() => {
    if (status === "connected") {
      fetchIssues();
    }
  }, [status, fetchIssues]);

  useEffect(() => {
    const onUpdate = (data: any) => {
      if (
        data.project_id &&
        currentProjectId &&
        data.project_id !== currentProjectId
      ) {
        return;
      }
      console.log("Issues updated via SSE");
      fetchIssues();
    };
    const unsubUpsert = sseManager.on("issue_upserted", onUpdate);
    const unsubDelete = sseManager.on("issue_deleted", onUpdate);
    return () => {
      unsubUpsert();
      unsubDelete();
    };
  }, [fetchIssues, currentProjectId]);

  const { epics, groupedIssues, unassigned } = useMemo(() => {
    const epics = issues
      .filter((i) => i.type === "epic" && i.status !== "closed")
      .sort((a, b) => a.id.localeCompare(b.id)); // Sort by ID
    const otherIssues = issues.filter((i) => i.type !== "epic");

    const grouped: Record<string, Issue[]> = {};
    const unassigned: Issue[] = [];

    otherIssues.forEach((issue) => {
      if (
        filterText &&
        !issue.title.toLowerCase().includes(filterText.toLowerCase()) &&
        !issue.id.toLowerCase().includes(filterText.toLowerCase())
      ) {
        return;
      }

      if (issue.parent) {
        if (!grouped[issue.parent]) {
          grouped[issue.parent] = [];
        }
        grouped[issue.parent].push(issue);
      } else {
        unassigned.push(issue);
      }
    });

    return { epics, groupedIssues: grouped, unassigned };
  }, [issues, filterText]);

  const getColumns = (groupIssues: Issue[]) => {
    const byStage: Record<string, Issue[]> = {
      todo: [],
      doing: [],
      review: [],
      done: [],
    };

    groupIssues.forEach((issue) => {
      const stage = issue.stage || "todo";
      if (byStage[stage]) {
        byStage[stage].push(issue);
      } else {
        // Fallback
        byStage["todo"].push(issue);
      }
    });

    // Sort
    Object.keys(byStage).forEach((key) => {
      byStage[key].sort((a, b) =>
        a.id.localeCompare(b.id, undefined, { numeric: true })
      );
    });

    return [
      { id: "todo", title: "To Do", items: byStage.todo },
      { id: "doing", title: "Doing", items: byStage.doing },
      { id: "review", title: "Review", items: byStage.review },
      { id: "done", title: "Done", items: byStage.done },
    ];
  };

  if (
    status === "connecting" ||
    (status === "connected" && loading && !error)
  ) {
    return (
      <div className="flex h-full items-center justify-center bg-canvas">
        <div className="flex flex-col items-center gap-4">
          <Spinner intent={Intent.PRIMARY} size={50} />
          <p className="text-text-muted animate-pulse">Loading Overview...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="h-full flex flex-col font-sans overflow-hidden bg-canvas">
      <IssueDetailModal
        issueId={focusedIssueId}
        onClose={() => setFocusedIssueId(null)}
      />

      <CreateIssueDialog
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={fetchIssues}
      />

      {/* Page Header */}
      <header className="px-6 py-6 flex justify-between items-end shrink-0 z-10 border-b border-border-subtle bg-surface/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-2xl font-bold text-text-primary tracking-tight mb-1">
              Overview
            </h1>
            <p className="text-sm text-text-muted">
              Track progress and manage tasks across the board.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            icon="plus"
            intent={Intent.PRIMARY}
            text="New Issue"
            onClick={() => setIsCreateOpen(true)}
          />
          <Popover
            position={Position.BOTTOM_RIGHT}
            content={
              <div className="p-2 bg-surface border border-border-subtle rounded shadow-sm">
                <InputGroup
                  leftIcon="filter"
                  placeholder="Filter issues..."
                  value={filterText}
                  onChange={(e) => setFilterText(e.target.value)}
                  className="bg-surface text-text-primary"
                />
              </div>
            }>
            <Button
              icon="filter"
              minimal
              text={filterText ? "Filtering..." : "Filter"}
              active={!!filterText}
            />
          </Popover>
        </div>
      </header>

      {/* Error State */}
      {error && (
        <div className="px-6 pt-4">
          <Callout intent="danger" title="Connection Error" icon="error">
            {error}
          </Callout>
        </div>
      )}

      {/* Board Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-8">
        {/* Epics Groups */}
        {epics.map((epic) => (
          <div key={epic.id} className="flex flex-col gap-4">
            <div
              className="flex items-center gap-4 p-3 rounded-lg border border-border-subtle bg-surface hover:bg-surface-hover hover:border-border-hover transition-all cursor-pointer shadow-sm group"
              onClick={() => setFocusedIssueId(epic.id)}>
              <div className="flex items-center justify-center bg-primary/10 text-primary font-mono text-sm font-bold px-2 py-1 rounded">
                {epic.id}
              </div>
              <h2 className="text-lg font-bold text-text-primary m-0 group-hover:text-primary transition-colors">
                {epic.title}
              </h2>

              {/* Metadata Badges */}
              <div className="flex gap-2 ml-auto items-center">
                <span className="text-xs uppercase font-semibold text-text-muted bg-surface-raised px-2 py-1 rounded border border-border-subtle">
                  {epic.status}
                </span>
                {epic.tags && epic.tags.length > 0 && (
                  <div className="flex gap-1">
                    {epic.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-xs text-text-muted bg-surface-raised px-1.5 py-0.5 rounded-full border border-border-subtle">
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="h-px bg-border-subtle w-full" />

            <div className="flex flex-row gap-6 overflow-x-auto pb-2">
              {getColumns(groupedIssues[epic.id] || []).map((col) => (
                <KanbanColumn
                  key={col.id}
                  id={col.id}
                  title={col.title}
                  issues={col.items}
                  activeIssueId={focusedIssueId}
                  onIssueClick={(issue) => setFocusedIssueId(issue.id)}
                />
              ))}
            </div>
          </div>
        ))}

        {/* Unassigned Group */}
        {groupedIssues["undefined"]?.length > 0 || unassigned.length > 0 ? (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3 text-text-primary">
              <h2 className="text-lg font-bold m-0 text-text-muted">
                Unassigned / Others
              </h2>
            </div>
            <div className="h-px bg-border-subtle w-full" />

            <div className="flex flex-row gap-6 overflow-x-auto pb-2">
              {getColumns([
                ...(groupedIssues["undefined"] || []),
                ...unassigned,
              ]).map((col) => (
                <KanbanColumn
                  key={col.id}
                  id={col.id}
                  title={col.title}
                  issues={col.items}
                  activeIssueId={focusedIssueId}
                  onIssueClick={(issue) => setFocusedIssueId(issue.id)}
                />
              ))}
            </div>
          </div>
        ) : null}

        {epics.length === 0 && unassigned.length === 0 && !loading && (
          <div className="text-center text-text-muted py-10">
            No issues found. Create one to get started!
          </div>
        )}
      </div>
    </main>
  );
}
