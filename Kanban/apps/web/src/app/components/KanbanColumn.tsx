import React, { useMemo } from "react";
import { Issue } from "../types";
import KanbanCard from "./KanbanCard";

interface KanbanColumnProps {
  id: string;
  title: string;
  issues: Issue[];
  activeIssueId?: string | null;
  onIssueClick?: (issue: Issue) => void;
}

const getColumnColor = (id: string) => {
  switch (id) {
    case "todo":
      return "bg-slate-500";
    case "doing":
      return "bg-blue-500";
    case "review":
      return "bg-amber-500";
    case "done":
      return "bg-emerald-500";
    default:
      return "bg-slate-500";
  }
};

interface IssueNodeProps {
  issue: Issue;
  childrenMap: Map<string, Issue[]>;
  depth?: number;
  activeIssueId?: string | null;
  onIssueClick?: (issue: Issue) => void;
}

const IssueNode = ({
  issue,
  childrenMap,
  depth = 0,
  activeIssueId,
  onIssueClick,
}: IssueNodeProps) => {
  const children = childrenMap.get(issue.id) || [];
  const hasChildren = children.length > 0;
  const isActive = activeIssueId === issue.id;

  return (
    <div
      className={`flex flex-col gap-2 ${
        depth > 0 ? "ml-3 pl-2 border-l border-border-subtle" : ""
      }`}>
      <div
        onClick={(e) => {
          e.stopPropagation();
          onIssueClick?.(issue);
        }}
        className={`transition-all duration-200 rounded-xl ${
          isActive
            ? "ring-2 ring-accent shadow-[0_0_15px_rgba(59,130,246,0.3)] bg-accent/5"
            : ""
        }`}>
        <KanbanCard issue={issue} />
      </div>
      {hasChildren && (
        <div className="flex flex-col gap-2">
          {children.map((child) => (
            <IssueNode
              key={child.id}
              issue={child}
              childrenMap={childrenMap}
              depth={depth + 1}
              activeIssueId={activeIssueId}
              onIssueClick={onIssueClick}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default function KanbanColumn({
  id,
  title,
  issues,
  activeIssueId,
  onIssueClick,
}: KanbanColumnProps) {
  const accentColor = getColumnColor(id);

  const { roots, childrenMap } = useMemo(() => {
    const map = new Map<string, Issue>();
    issues.forEach((i) => map.set(i.id, i));

    const roots: Issue[] = [];
    const childrenMap = new Map<string, Issue[]>();

    issues.forEach((i) => {
      if (i.parent && map.has(i.parent)) {
        const list = childrenMap.get(i.parent) || [];
        list.push(i);
        childrenMap.set(i.parent, list);
      } else {
        roots.push(i);
      }
    });
    return { roots, childrenMap };
  }, [issues]);

  return (
    <div className="flex flex-col flex-1 min-w-[280px] h-full">
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${accentColor} shadow-[0_0_8px_rgba(0,0,0,0.5)]`}
          />
          <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider m-0">
            {title}
          </h3>
        </div>
        <span className="bg-surface-highlight text-text-muted text-xs px-2 py-0.5 rounded-full font-mono">
          {issues.length}
        </span>
      </div>

      <div className="flex-1 glass-panel rounded-xl p-2 overflow-y-auto custom-scrollbar flex flex-col gap-2 border-t-4 border-t-transparent hover:border-t-border-subtle transition-colors">
        {roots.map((issue) => (
          <IssueNode
            key={issue.id}
            issue={issue}
            childrenMap={childrenMap}
            activeIssueId={activeIssueId}
            onIssueClick={onIssueClick}
          />
        ))}

        {issues.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-text-muted opacity-40">
            <span className="text-4xl mb-2">∅</span>
            <span className="text-xs">No issues</span>
          </div>
        )}
      </div>
    </div>
  );
}
