import React from "react";
import { Tag, Icon, Intent, Button, Menu, MenuItem, Popover, Position } from "@blueprintjs/core";
import { Issue } from "../types";
import { useTerms } from "../contexts/TermContext";

interface KanbanCardProps {
  issue: Issue;
}

const getStatusIntent = (status: string): Intent => {
// ... existing getStatusIntent ...
};

const getTypeIcon = (type: string) => {
// ... existing getTypeIcon ...
};

const getTypeColor = (type: string) => {
// ... existing getTypeColor ...
};

export default function KanbanCard({ issue }: KanbanCardProps) {
  const { t } = useTerms();
  
  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData("text/plain", issue.id);
    e.dataTransfer.effectAllowed = "move";
  };

  return (
    <div 
      draggable={true}
      onDragStart={handleDragStart}
      className="group relative glass-card rounded-xl p-3 cursor-pointer transition-all duration-200 hover:shadow-lg hover:border-accent/30 hover:bg-surface-highlight/50 border-l-4 border-l-transparent hover:border-l-accent active:cursor-grabbing"
    >
      
      {/* Header: ID, Type, Actions */}
      <div className="flex flex-row justify-between items-start mb-2">
        <div className="flex flex-row items-center gap-2">
          <span className="font-mono text-[10px] text-text-muted opacity-70 group-hover:opacity-100 transition-opacity">
            {issue.id}
          </span>
          <div className={`flex flex-row items-center gap-1 text-[10px] uppercase font-bold tracking-wider ${getTypeColor(issue.type)}`}>
            <Icon icon={getTypeIcon(issue.type)} size={10} />
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
            {t(issue.status, issue.status)}
        </Tag>
      </div>
    </div>
  );
}
