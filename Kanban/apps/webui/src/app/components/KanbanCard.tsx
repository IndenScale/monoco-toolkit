import React from "react";
import {
  Tag,
  Icon,
  Intent,
  Button,
  Menu,
  MenuItem,
  Popover,
  Position,
} from "@blueprintjs/core";
import { Issue } from "../types";
import { useTerms } from "../contexts/TermContext";
import { useBridge } from "../contexts/BridgeContext";

interface KanbanCardProps {
  issue: Issue;
}

const getStatusIntent = (status: string): Intent => {
  switch (status?.toLowerCase()) {
    case "open":
    case "draft":
      return Intent.NONE;
    case "in_progress":
    case "doing":
      return Intent.PRIMARY;
    case "review":
      return Intent.WARNING;
    case "done":
    case "closed":
      return Intent.SUCCESS;
    default:
      return Intent.NONE;
  }
};

const getTypeIcon = (type: string) => {
  switch (type?.toLowerCase()) {
    case "epic":
      return "crown";
    case "feature":
      return "star";
    case "chore":
      return "build";
    case "fix":
      return "wrench";
    default:
      return "document";
  }
};

const getTypeColor = (type: string) => {
  switch (type?.toLowerCase()) {
    case "epic":
      return "text-purple-400";
    case "feature":
      return "text-blue-400";
    case "chore":
      return "text-gray-400";
    case "fix":
      return "text-red-400";
    default:
      return "text-text-muted";
  }
};

export default function KanbanCard({ issue }: KanbanCardProps) {
  const { t } = useTerms();
  const { isVsCode } = useBridge();

  const handleDragStart = (e: React.DragEvent) => {
    // 1. Text fallback
    e.dataTransfer.setData("text/plain", issue.id);

    // 2. URI list if path exists
    if (issue.path) {
      const config = (window as any).monocoConfig;
      const root = config?.rootPath;
      let fullPath = issue.path;

      if (root && !fullPath.startsWith("/") && !fullPath.match(/^[a-zA-Z]:/)) {
        const sep = root.includes("\\") ? "\\" : "/";
        fullPath = root + (root.endsWith(sep) ? "" : sep) + issue.path;
      }

      // Simple URI construction
      const fileUri = fullPath.match(/^[a-zA-Z]:/)
        ? `file:///${fullPath.replace(/\\/g, "/")}`
        : `file://${fullPath}`;

      e.dataTransfer.setData("text/uri-list", fileUri);
    }

    // 3. Internal data for drop targets
    e.dataTransfer.setData("application/monoco-issue", JSON.stringify(issue));
    e.dataTransfer.effectAllowed = "move";
  };

  return (
    <div
      draggable={true}
      onDragStart={handleDragStart}
      className={`group relative glass-card rounded-xl cursor-pointer transition-all duration-200 hover:shadow-lg hover:border-accent/30 hover:bg-surface-highlight/50 border-l-4 border-l-transparent hover:border-l-accent active:cursor-grabbing ${
        isVsCode ? "p-2 mb-2" : "p-3 mb-3"
      }`}>
      {/* Header: ID, Type, Actions */}
      <div className="flex flex-row justify-between items-start mb-1">
        <div className="flex flex-row items-center gap-2">
          <span className="font-mono text-[10px] text-text-muted opacity-70 group-hover:opacity-100 transition-opacity">
            {issue.id}
          </span>
          <div
            className={`flex flex-row items-center gap-1 text-[10px] uppercase font-bold tracking-wider ${getTypeColor(
              issue.type,
            )}`}>
            {/* Hide Icon in extreme compact mode if needed, but keeping for now */}
            {!isVsCode && <Icon icon={getTypeIcon(issue.type)} size={10} />}
            <span>{t(issue.type, issue.type)}</span>
          </div>
        </div>

        <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute right-2 top-2">
          <Popover
            content={
              <Menu>
                <MenuItem icon="edit" text="Edit" />
                <MenuItem icon="trash" text="Delete" intent="danger" />
              </Menu>
            }
            position={Position.BOTTOM_RIGHT}>
            <Button icon="more" minimal small className="!min-h-0 !h-6 !w-6" />
          </Popover>
        </div>
      </div>

      {/* Title */}
      <h4
        className={`text-text-primary font-medium leading-relaxed group-hover:text-white transition-colors ${
          isVsCode ? "text-xs mb-1" : "text-sm mb-3"
        }`}>
        {issue.title}
      </h4>

      {/* Footer: Status, Metadata */}
      {/* In VS Code Compact Mode, we might want to hide the footer or simplify it */}
      <div
        className={`flex flex-row justify-between items-center border-t border-white/5 ${
          isVsCode ? "pt-1" : "pt-2"
        }`}>
        <div className="flex flex-row items-center gap-2">
          {/* Only show Parent in non-compact mode or if it fits */}
          {!isVsCode && issue.parent && (
            <div
              className="flex flex-row items-center gap-1 text-[10px] text-text-muted"
              title={`Parent: ${issue.parent}`}>
              <Icon icon="git-merge" size={10} />
              <span className="font-mono truncate max-w-[60px]">
                {issue.parent}
              </span>
            </div>
          )}
        </div>

        <Tag
          minimal
          intent={getStatusIntent(issue.status)}
          className={`!bg-white/5 !text-[10px] !min-h-0 font-semibold uppercase tracking-wide border border-white/10 group-hover:border-white/20 ${
            isVsCode ? "!h-4 !px-1 text-[9px]" : "!h-5"
          }`}>
          {t(issue.status, issue.status)}
        </Tag>
      </div>
    </div>
  );
}
