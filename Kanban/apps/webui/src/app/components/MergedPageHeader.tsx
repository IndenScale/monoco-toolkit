"use client";

import React from "react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ChevronDown, Briefcase } from "lucide-react";
import { useDaemonStore } from "@monoco-io/kanban-core";
import ProjectTreeSelector from "./ProjectTreeSelector";

interface MergedPageHeaderProps {
  title: string;
  children?: React.ReactNode;
  bottomContent?: React.ReactNode;
}

export default function MergedPageHeader({
  title,
  children,
  bottomContent,
}: MergedPageHeaderProps) {
  const { projects, currentProjectId } = useDaemonStore();
  const currentProject = projects?.find((p: any) => p.id === currentProjectId);

  return (
    <header className="px-6 py-6 shrink-0 z-10 border-b border-border-subtle bg-surface/50 backdrop-blur-sm">
      <div
        className={`flex justify-between items-center ${
          bottomContent ? "mb-4" : ""
        }`}>
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">
            {title}
          </h1>

          <div className="flex items-center">
            <Popover>
              <PopoverTrigger asChild>
                <div className="flex items-center gap-2 cursor-pointer hover:bg-surface-highlight px-3 py-1.5 rounded-full transition-all border border-transparent hover:border-border-subtle bg-surface/50 shadow-sm group">
                  <div className="w-5 h-5 flex items-center justify-center rounded-full bg-blue-500/10 text-blue-600 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                    <Briefcase size={10} />
                  </div>
                  <span className="font-semibold text-sm text-text-primary max-w-[200px] truncate">
                    {currentProject?.name || "Select Project"}
                  </span>
                  <ChevronDown size={12} className="text-text-muted" />
                </div>
              </PopoverTrigger>
              <PopoverContent className="w-[300px] p-0" align="start">
                <ProjectTreeSelector />
              </PopoverContent>
            </Popover>
          </div>
        </div>

        <div className="flex items-center gap-3">{children}</div>
      </div>

      {bottomContent && <div>{bottomContent}</div>}
    </header>
  );
}
