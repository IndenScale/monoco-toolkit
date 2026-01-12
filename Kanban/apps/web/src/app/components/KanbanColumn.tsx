import React, { useMemo } from "react";
import { Issue } from "../types";
import KanbanCard from "./KanbanCard";

interface KanbanColumnProps {
  id: string;
  title: string;
  issues: Issue[];
  activeIssueId?: string | null;
  onIssueClick?: (issue: Issue) => void;
  onDrop?: (issueId: string, stageId: string) => void;
}

// ... (getCOlumnColor and IssueNode remain same) ...

export default function KanbanColumn({
  id,
  title,
  issues,
  activeIssueId,
  onIssueClick,
  onDrop,
}: KanbanColumnProps) {
  const accentColor = getColumnColor(id);

  const { roots, childrenMap } = useMemo(() => {
    // ... same logic ...
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

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const issueId = e.dataTransfer.getData("text/plain");
    if (issueId && onDrop) {
      onDrop(issueId, id);
    }
  };

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

      <div 
        className="flex-1 glass-panel rounded-xl p-2 overflow-y-auto custom-scrollbar flex flex-col gap-2 border-t-4 border-t-transparent hover:border-t-border-subtle transition-colors"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
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
