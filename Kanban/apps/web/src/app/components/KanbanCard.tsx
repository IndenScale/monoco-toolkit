import React from "react";
import { Tag, Icon, Intent, Button, Menu, MenuItem, Popover, Position } from "@blueprintjs/core";
import { Issue } from "../types";

interface KanbanCardProps {
  issue: Issue;
}

const getStatusIntent = (status: string): Intent => {
  switch (status.toLowerCase()) {
    case "done":
    case "closed":
      return Intent.SUCCESS;
    case "doing":
    case "open":
      return Intent.PRIMARY;
    case "review":
      return Intent.WARNING;
    case "todo":
    case "backlog":
    default:
      return Intent.NONE;
  }
};

const getTypeIcon = (type: string) => {
  switch (type.toLowerCase()) {
    case "bug": return "error";
    case "feature": return "clean";
    case "task": return "tick";
    default: return "document";
  }
};

const getTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "bug": return "text-red-400";
      case "feature": return "text-blue-400";
      case "task": return "text-emerald-400";
      default: return "text-slate-400";
    }
  };

export default function KanbanCard({ issue }: KanbanCardProps) {
  return (
    <div className="group relative glass-card rounded-xl p-3 cursor-pointer transition-all duration-200 hover:shadow-lg hover:border-accent/30 hover:bg-surface-highlight/50 border-l-4 border-l-transparent hover:border-l-accent">
      
      {/* Header: ID, Type, Actions */}
      <div className="flex flex-row justify-between items-start mb-2">
        <div className="flex flex-row items-center gap-2">
          <span className="font-mono text-[10px] text-text-muted opacity-70 group-hover:opacity-100 transition-opacity">
            {issue.id}
          </span>
          <div className={`flex flex-row items-center gap-1 text-[10px] uppercase font-bold tracking-wider ${getTypeColor(issue.type)}`}>
            <Icon icon={getTypeIcon(issue.type)} size={10} />
            <span>{issue.type}</span>
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
                position={Position.BOTTOM_RIGHT}
            >
                <Button icon="more" minimal small className="!min-h-0 !h-6 !w-6" />
            </Popover>
        </div>
      </div>
      
      {/* Title */}
      <h4 className="text-text-primary text-sm font-medium leading-relaxed mb-3 group-hover:text-white transition-colors">
        {issue.title}
      </h4>

      {/* Footer: Status, Metadata */}
      <div className="flex flex-row justify-between items-center pt-2 border-t border-white/5">
        <div className="flex flex-row items-center gap-2">
           {issue.parent && (
               <div className="flex flex-row items-center gap-1 text-[10px] text-text-muted" title={`Parent: ${issue.parent}`}>
                   <Icon icon="git-merge" size={10} />
                   <span className="font-mono truncate max-w-[60px]">{issue.parent}</span>
               </div>
           )}
        </div>
        
        <Tag 
            minimal 
            intent={getStatusIntent(issue.status)}
            className="!bg-white/5 !text-[10px] !h-5 !min-h-0 font-semibold uppercase tracking-wide border border-white/10 group-hover:border-white/20"
        >
            {issue.status}
        </Tag>
      </div>
    </div>
  );
}
