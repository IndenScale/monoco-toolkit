import React, { useMemo } from "react";
import { Issue } from "../types";
import KanbanCard from "./KanbanCard";
import { useBridge } from "../contexts/BridgeContext";

interface KanbanColumnProps {
  id: string;
  title: string;
  issues: Issue[];
  activeIssueId?: string | null;
  onIssueClick?: (issue: Issue) => void;
  onDrop?: (issueId: string, stageId: string) => void;
}

const getColumnColor = (id: string) => {
  switch (id) {
    case "todo":
      return "bg-slate-500";
    case "doing":
      return "bg-blue-500";
    case "review":
      return "bg-yellow-500";
    case "done":
      return "bg-green-500";
    default:
      return "bg-gray-500";
  }
};

interface IssueNodeProps {
  issue: Issue;
  childrenMap: Map<string, Issue[]>;
  activeIssueId?: string | null;
  onIssueClick?: (issue: Issue) => void;
  level?: number;
}

const IssueNode = ({
  issue,
  childrenMap,
  activeIssueId,
  onIssueClick,
  level = 0,
}: IssueNodeProps) => {
  const children = childrenMap.get(issue.id) || [];

  return (
    <div className="flex flex-col gap-2">
      <div onClick={() => onIssueClick && onIssueClick(issue)}>
        <KanbanCard issue={issue} />
      </div>

      {children.length > 0 && (
        <div className="pl-4 border-l border-white/10 flex flex-col gap-2">
          {children.map((child) => (
            <IssueNode
              key={child.id}
              issue={child}
              childrenMap={childrenMap}
              activeIssueId={activeIssueId}
              onIssueClick={onIssueClick}
              level={level + 1}
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
  onDrop,
}: KanbanColumnProps) {
  const [isDragOver, setIsDragOver] = React.useState(false);
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

  const { isVsCode } = useBridge();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    // Only set to false if we are leaving the main container
    // This is a bit tricky with children, but for a simple column it might be enough
    // improved check: if the related target is not inside the current component
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setIsDragOver(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const issueId = e.dataTransfer.getData("text/plain");
    console.log(`Dropped issue ${issueId} on column ${id}`);
    if (issueId && onDrop) {
      onDrop(issueId, id);
    }
  };

  return (
    <div
      className={`flex flex-col flex-1 h-full transition-colors duration-200 rounded-xl ${
        isVsCode ? "min-w-[200px]" : "min-w-[280px]"
      } ${isDragOver ? "bg-white/5 ring-2 ring-primary/50" : ""}`}
      onDragOver={handleDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}>
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
        className={`flex-1 glass-panel rounded-xl p-2 overflow-y-auto custom-scrollbar flex flex-col gap-2 border-t-4 transition-colors ${
          isDragOver
            ? "border-t-primary bg-primary/5"
            : "border-t-transparent hover:border-t-border-subtle"
        }`}>
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
