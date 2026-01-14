"use client";

import MergedPageHeader from "../components/MergedPageHeader";
import React, { useState, useMemo } from "react";
import { useKanbanStore, useKanbanSync } from "@monoco-io/kanban-core";
import {
  HTMLTable,
  Tag,
  InputGroup,
  Spinner,
  Intent,
  Icon,
  Button,
  ButtonGroup,
  Collapse,
} from "@blueprintjs/core";
import IssueDetailModal from "../components/IssueDetailModal";
import { Issue } from "../types";

export default function DetailedView() {
  // Sync data with Daemon
  useKanbanSync();

  const { issues, isLoading } = useKanbanStore();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedIssueId, setSelectedIssueId] = useState<string | null>(null);
  const [expandedEpics, setExpandedEpics] = useState<Set<string>>(new Set());

  const toggleEpic = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newExpanded = new Set(expandedEpics);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedEpics(newExpanded);
  };

  const treeData = useMemo(() => {
    if (!issues.length) return [];

    // 1. Filter first if needed (optional, or filter the tree later)
    // For now, let's filter the flat list first for simplicity,
    // but this might break the tree if parent is filtered out.
    // Better approach: Build tree, then filter?
    // Or: Filter flat list, but include parents of matches?
    // Let's just filter flat list for now. If parent is missing, child becomes a root or orphan.
    let filtered = issues;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = issues.filter(
        (i) =>
          i.title.toLowerCase().includes(term) ||
          i.id.toLowerCase().includes(term)
      );
    }

    // 2. Build Tree
    const issueMap = new Map<string, Issue & { children: any[] }>();
    filtered.forEach((i) => {
      issueMap.set(i.id, { ...i, children: [] });
    });

    const roots: (Issue & { children: any[] })[] = [];

    // Re-iterate to link parents
    // Note: We iterate 'filtered'. If a parent is not in 'filtered', the child becomes a root in this view.
    filtered.forEach((i) => {
      const node = issueMap.get(i.id)!;
      if (i.parent && issueMap.has(i.parent)) {
        const parent = issueMap.get(i.parent)!;
        parent.children.push(node);
      } else {
        roots.push(node);
      }
    });

    // 3. Sort Function
    const sortFn = (a: Issue, b: Issue) => {
      // Primary: Type
      if (a.type !== b.type) {
        return a.type.localeCompare(b.type);
      }
      // Secondary: ID (Number)
      // Assuming ID is like 'PROJ-123', we want numeric sort if possible
      return a.id.localeCompare(b.id, undefined, { numeric: true });
    };

    // Separate Epics and Unarchived from roots
    const epics: (Issue & { children: any[] })[] = [];
    const unarchived: (Issue & { children: any[] })[] = [];

    roots.forEach((root) => {
      if (root.type.toLowerCase() === "epic") {
        epics.push(root);
      } else {
        unarchived.push(root);
      }
    });

    // Sort children recursively
    const sortChildren = (nodes: any[]) => {
      nodes.sort(sortFn);
      nodes.forEach((n) => {
        if (n.children.length > 0) {
          sortChildren(n.children);
        }
      });
    };

    // Sort Epics
    sortChildren(epics);

    // Sort Unarchived items
    sortChildren(unarchived);

    const finalRoots = [...epics];

    if (unarchived.length > 0) {
      const unarchivedRoot: any = {
        id: "unarchived",
        title: "未归档",
        type: "group",
        status: "",
        stage: "",
        created_at: "",
        children: unarchived,
      };
      finalRoots.push(unarchivedRoot);
    }

    return finalRoots;
  }, [issues, searchTerm]);

  // Auto-expand all if searching, otherwise maybe collapse?
  // Let's default to expanded for now or handle in effect.
  // Actually, let's just leave it manual or default all expanded.

  const getStatusIntent = (status: string) => {
    switch (status.toLowerCase()) {
      case "open":
        return Intent.NONE;
      case "in_progress":
        return Intent.PRIMARY;
      case "done":
        return Intent.SUCCESS;
      case "closed":
        return Intent.DANGER;
      default:
        return Intent.NONE;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "feat":
        return "star";
      case "fix":
        return "wrench";
      case "chore":
        return "clean";
      case "docs":
        return "document";
      case "refactor":
        return "git-merge";
      case "epic":
        return "crown"; // Icon for Epic
      case "group":
        return "folder-close";
      default:
        return "help";
    }
  };

  if (isLoading && issues.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner size={50} intent={Intent.PRIMARY} />
      </div>
    );
  }

  const renderRow = (issue: any, level: number = 0) => {
    const hasChildren = issue.children && issue.children.length > 0;
    const isExpanded = expandedEpics.has(issue.id) || searchTerm !== ""; // Auto expand on search

    // Indentation padding
    const paddingLeft = `${level * 24 + 12}px`;

    return (
      <React.Fragment key={issue.id}>
        <tr
          className={`hover:bg-surface-highlight cursor-pointer transition-colors ${
            level === 0 ? "bg-surface-subtle/30" : ""
          }`}
          onClick={() => setSelectedIssueId(issue.id)}>
          <td
            style={{ paddingLeft }}
            className="font-mono text-xs text-text-muted whitespace-nowrap">
            <div className="flex items-center gap-2">
              {hasChildren && (
                <Button
                  minimal
                  small
                  icon={isExpanded ? "chevron-down" : "chevron-right"}
                  onClick={(e) => toggleEpic(issue.id, e)}
                />
              )}
              {!hasChildren && level > 0 && <div className="w-[20px]" />}{" "}
              {/* Spacer */}
              {issue.id}
            </div>
          </td>
          <td>
            <div className="flex items-center gap-2">
              <Icon
                icon={getTypeIcon(issue.type) as any}
                size={14}
                className="text-text-muted"
              />
              <span className="uppercase text-xs font-semibold text-text-secondary">
                {issue.type}
              </span>
            </div>
          </td>
          <td className="font-medium text-text-primary">{issue.title}</td>
          <td>
            <Tag intent={getStatusIntent(issue.status)} minimal round>
              {issue.status}
            </Tag>
          </td>
          <td className="text-text-secondary">{issue.stage || "-"}</td>
          <td className="text-text-muted text-sm">{issue.created_at || "-"}</td>
        </tr>
        {hasChildren &&
          (isExpanded || searchTerm) &&
          issue.children.map((child: any) => renderRow(child, level + 1))}
      </React.Fragment>
    );
  };

  return (
    <main className="h-full flex flex-col font-sans overflow-hidden bg-canvas">
      {/* Header */}
      <MergedPageHeader
        title="Detailed"
        children={
          <div className="flex gap-2">
            <Button icon="export" text="Export" minimal />
            <Button icon="plus" intent={Intent.PRIMARY} text="New Issue" />
          </div>
        }
        bottomContent={
          <div className="flex gap-4 items-center">
            <div className="w-64">
              <InputGroup
                leftIcon="search"
                placeholder="Filter issues..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
        }
      />

      {/* Table */}
      <div className="flex-1 overflow-auto px-6 py-4">
        <HTMLTable interactive compact striped className="w-full">
          <thead>
            <tr className="text-text-muted">
              <th>ID</th>
              <th>Type</th>
              <th>Title</th>
              <th>Status</th>
              <th>Stage</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {treeData.map((root) => renderRow(root, 0))}
            {treeData.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center py-8 text-text-muted">
                  No issues found matching your criteria.
                </td>
              </tr>
            )}
          </tbody>
        </HTMLTable>
      </div>

      <IssueDetailModal
        issueId={selectedIssueId}
        onClose={() => setSelectedIssueId(null)}
      />
    </main>
  );
}
