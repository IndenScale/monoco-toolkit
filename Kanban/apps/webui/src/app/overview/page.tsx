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
import { useTerms } from "../contexts/TermContext";

export default function OverviewPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [focusedIssueId, setFocusedIssueId] = useState<string | null>(null);
  const [collapsedEpics, setCollapsedEpics] = useState<Record<string, boolean>>(
    {}
  );
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [filterText, setFilterText] = useState("");
  const { t } = useTerms();

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

  // ... inside component ...
  const handleIssueDrop = async (issueId: string, stageId: string) => {
    if (status !== "connected") return;

    // Find issue to verify change is needed
    const issue = issues.find((i) => i.id === issueId);
    if (!issue || issue.stage === stageId) return;

    try {
      const res = await fetch(`${daemonUrl}/api/v1/issues/${issueId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          stage: stageId,
          project_id: currentProjectId,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to update issue stage");
      }

      // SSE will handle the UI update
    } catch (err: any) {
      console.error(err);
      // Dynamic import to avoid SSR issues with Blueprint Toaster if any
      const { OverlayToaster, Position: ToasterPosition } = await import(
        "@blueprintjs/core"
      );
      const toaster = await OverlayToaster.createAsync({
        position: ToasterPosition.TOP,
      });
      toaster.show({
        message: `Failed to move ${issueId}: ${err.message}`,
        intent: "danger",
        icon: "error",
      });
    }
  };

  const getColumns = (groupIssues: Issue[]) => {
    // ... existing getColumns logic ...
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
      { id: "todo", title: t("todo", "To Do"), items: byStage.todo },
      { id: "doing", title: t("doing", "Doing"), items: byStage.doing },
      { id: "review", title: t("review", "Review"), items: byStage.review },
      { id: "done", title: t("done", "Done"), items: byStage.done },
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
              onClick={() =>
                setCollapsedEpics((prev) => ({
                  ...prev,
                  [epic.id]: !prev[epic.id],
                }))
              }>
              <div className="flex items-center justify-center bg-primary/10 text-primary font-mono text-sm font-bold px-2 py-1 rounded">
                <div
                  className={`transition-transform duration-200 ${
                    collapsedEpics[epic.id] ? "-rotate-90" : ""
                  }`}>
                  ▼
                </div>
                <div className="ml-2">{epic.id}</div>
              </div>
              <h2 className="text-lg font-bold text-text-primary m-0 group-hover:text-primary transition-colors">
                {epic.title}
              </h2>

              {/* Metadata Badges */}
              <div className="flex gap-2 ml-auto items-center">
                <span className="text-xs uppercase font-semibold text-text-muted bg-surface-raised px-2 py-1 rounded border border-border-subtle">
                  {epic.status}
                </span>
                <Button
                  icon="maximize"
                  minimal
                  small
                  className="!text-text-muted hover:!text-primary"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFocusedIssueId(epic.id);
                  }}
                />
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

            {!collapsedEpics[epic.id] && (
              <>
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
                      onDrop={handleIssueDrop}
                    />
                  ))}
                </div>
              </>
            )}
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
                  onDrop={handleIssueDrop}
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
