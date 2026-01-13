"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import {
  Spinner,
  Intent,
  Callout,
  Button,
  InputGroup,
  Popover,
} from "@blueprintjs/core";
import {
  useDaemonStore,
  useSSEConnection,
  sseManager,
} from "@monoco-io/kanban-core";
import KanbanColumn from "../components/KanbanColumn";
import IssueDetailModal from "../components/IssueDetailModal";
import CreateIssueDialog from "../components/CreateIssueDialog";
import { Issue } from "../types";
import { useTerms } from "../contexts/TermContext";

const parseSearchQuery = (query: string) => {
  // Regex to match quoted strings OR non-whitespace/non-quote sequences
  // This basically splits by spaces but Respects Quotes
  // e.g. 'foo "bar baz"' -> ['foo', '"bar baz"']
  // e.g. '-"bar baz"' -> ['-"bar baz"']
  const regex = /([+\-]?"[^"]*")|([^\s]+)/g;
  const matches = query.match(regex) || [];

  const tokens = matches.map((t) => t.toLowerCase());

  const explicitPositives: string[] = [];
  const terms: string[] = [];
  const negatives: string[] = [];

  tokens.forEach((token) => {
    if (token.startsWith("-")) {
      // Exclude
      // Remove '-' and strip quotes if present
      let term = token.slice(1);
      if (term.startsWith('"') && term.endsWith('"')) {
        term = term.slice(1, -1);
      }
      if (term) negatives.push(term);
    } else if (token.startsWith("+")) {
      // Explicit Include
      // Remove '+' and strip quotes if present
      let term = token.slice(1);
      if (term.startsWith('"') && term.endsWith('"')) {
        term = term.slice(1, -1);
      }
      if (term) explicitPositives.push(term);
    } else {
      // Neutral Term (Nice to have)
      let term = token;
      // Strip quotes
      if (term.startsWith('"') && term.endsWith('"')) {
        term = term.slice(1, -1);
      }
      if (term) terms.push(term);
    }
  });

  return { explicitPositives, terms, negatives };
};

const checkMatch = (
  issue: Issue,
  explicitPositives: string[],
  terms: string[],
  negatives: string[]
) => {
  const content = [
    issue.id,
    issue.title,
    issue.status,
    issue.body || "",
    issue.raw_content || "",
    ...(issue.tags || []),
    ...(issue.dependencies || []),
  ]
    .join(" ")
    .toLowerCase();

  // 1. Check Negatives
  if (negatives.some((t) => content.includes(t))) return false;

  // 2. Check Explicit Positives (Must include ALL)
  if (!explicitPositives.every((t) => content.includes(t))) return false;

  // 3. Check Terms
  // Rule: If explicit positives exist, terms are optional.
  //       If NO explicit positives, terms act as Implicit OR (at least one must match)
  const hasExplicit = explicitPositives.length > 0;

  if (terms.length > 0) {
    if (!hasExplicit) {
      // Implicit OR (Standard Search Engine behavior)
      return terms.some((t) => content.includes(t));
    }
    // Else: we have explicit filters, so "terms" are just nice-to-have,
    // they don't filter out anything.
    // So we return true.
  }

  return true;
};

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
    // 1. Parse Query
    const { explicitPositives, terms, negatives } =
      parseSearchQuery(filterText);
    const hasFilter =
      explicitPositives.length > 0 || terms.length > 0 || negatives.length > 0;

    // 2. Classify Issues
    const allEpics = issues
      .filter((i) => i.type === "epic" && i.status !== "closed")
      .sort((a, b) => a.id.localeCompare(b.id));

    const allTasks = issues.filter((i) => i.type !== "epic");

    // 3. Determine Matches (independent of hierarchy)
    const epicMatches = new Set<string>();
    const taskMatches = new Set<string>();

    if (!hasFilter) {
      // optimization: match everything
      allEpics.forEach((e) => epicMatches.add(e.id));
      allTasks.forEach((t) => taskMatches.add(t.id));
    } else {
      allEpics.forEach((e) => {
        if (checkMatch(e, explicitPositives, terms, negatives))
          epicMatches.add(e.id);
      });
      allTasks.forEach((t) => {
        if (checkMatch(t, explicitPositives, terms, negatives))
          taskMatches.add(t.id);
      });
    }

    // 4. Resolve Visibility (Hierarchy Logic)
    // - Epic is visible if: It matches OR it has a matching child
    // - Task is visible if: It matches OR its parent matches
    const finalEpics: Issue[] = [];
    const grouped: Record<string, Issue[]> = {};
    const unassignedList: Issue[] = [];

    // Helper to check if epic has matching children
    const epicHasMatchingChildren = (epicId: string) => {
      return allTasks.some((t) => t.parent === epicId && taskMatches.has(t.id));
    };

    allEpics.forEach((epic) => {
      const selfMatch = epicMatches.has(epic.id);
      const childMatch = epicHasMatchingChildren(epic.id);

      if (selfMatch || childMatch) {
        finalEpics.push(epic);
        grouped[epic.id] = []; // Initialize group
      }
    });

    allTasks.forEach((task) => {
      const selfMatch = taskMatches.has(task.id);
      const parentMatch = task.parent && epicMatches.has(task.parent); // This logic implies "Search Epic" shows all its tasks

      if (selfMatch || parentMatch) {
        if (task.parent) {
          // Only add if the parent is actually an active epic we're tracking
          if (grouped[task.parent]) {
            grouped[task.parent].push(task);
          } else {
            // Parent might be closed or missing, treat as unassigned or invisible?
            // If parent matched but wasn't in 'finalEpics', that's impossible per logic above.
            // But if ONLY child matched and parent didn't, parent IS in finalEpics.
            // So this case handles matching tasks whose parent might be missing/closed.
            // If task matches, we want to see it.
            unassignedList.push(task);
          }
        } else {
          unassignedList.push(task);
        }
      }
    });

    return {
      epics: finalEpics,
      groupedIssues: grouped,
      unassigned: unassignedList,
    };
  }, [issues, filterText]);

  // ... inside component ...
  const handleIssueDrop = async (issueId: string, stageId: string) => {
    console.log(
      `handleIssueDrop called with issueId: ${issueId}, stageId: ${stageId}, status: ${status}`
    );
    if (status !== "connected") {
      console.warn("Daemon status is not connected, aborting drop");
      return;
    }

    // Find issue to verify change is needed
    const issue = issues.find((i) => i.id === issueId);
    if (!issue) {
      console.warn("Issue not found in local state");
      return;
    }
    if (issue.stage === stageId) {
      console.log("Issue already in target stage, ignoring");
      return;
    }

    // Optimistic update
    const previousIssues = [...issues];
    setIssues((prev) =>
      prev.map((i) => (i.id === issueId ? { ...i, stage: stageId } : i))
    );

    try {
      console.log(
        `Sending PATCH request to ${daemonUrl}/api/v1/issues/${issueId}`
      );
      const res = await fetch(`${daemonUrl}/api/v1/issues/${issueId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          stage: stageId,
          project_id: currentProjectId,
        }),
      });

      if (!res.ok) {
        // Revert on failure
        setIssues(previousIssues);
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to update issue stage");
      }
      console.log("Issue update successful");

      // SSE will handle the UI update or confirm it
    } catch (err: any) {
      // Revert on error
      setIssues(previousIssues);
      console.error("Error in handleIssueDrop:", err);
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
          <Popover
            content={
              <div className="p-3 bg-surface border border-border rounded-lg shadow-2xl min-w-[240px]">
                <div className="text-xs font-bold text-text-muted uppercase tracking-wider mb-3 border-b border-border-subtle pb-2">
                  Search Syntax
                </div>
                <ul className="list-none space-y-2 m-0 p-0 text-sm">
                  <li className="flex items-center justify-between gap-4">
                    <span className="text-text-secondary">Fuzzy match</span>
                    <code className="bg-surface-highlight px-1.5 py-0.5 rounded text-xs font-mono text-accent">
                      text
                    </code>
                  </li>
                  <li className="flex items-center justify-between gap-4">
                    <span className="text-text-secondary">Exact phrase</span>
                    <code className="bg-surface-highlight px-1.5 py-0.5 rounded text-xs font-mono text-accent">
                      "foo bar"
                    </code>
                  </li>
                  <li className="flex items-center justify-between gap-4">
                    <span className="text-text-secondary">Must include</span>
                    <code className="bg-surface-highlight px-1.5 py-0.5 rounded text-xs font-mono text-accent">
                      +term
                    </code>
                  </li>
                  <li className="flex items-center justify-between gap-4">
                    <span className="text-text-secondary">Exclude</span>
                    <code className="bg-surface-highlight px-1.5 py-0.5 rounded text-xs font-mono text-red-400">
                      -term
                    </code>
                  </li>
                </ul>
              </div>
            }
            interactionKind="hover"
            placement="bottom-start"
            minimal={true}
            popoverClassName="bp5-dark"
            targetTagName="div"
            modifiers={{
              offset: { enabled: true, options: { offset: [0, 4] } },
              flip: { enabled: true },
              preventOverflow: { enabled: true, options: { padding: 10 } },
            }}>
            <InputGroup
              leftIcon="filter"
              placeholder="Filter..."
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              className="w-64 bg-surface text-text-primary focus:border-accent"
              type="search"
            />
          </Popover>
          <Button
            icon="plus"
            intent={Intent.PRIMARY}
            text="New Issue"
            onClick={() => setIsCreateOpen(true)}
          />
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
