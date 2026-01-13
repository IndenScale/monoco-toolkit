"use client";

import React, { useState } from "react";
import { usePathname } from "next/navigation";
import { Icon, Tooltip, Position, Popover, Button, Classes } from "@blueprintjs/core";
import Link from "next/link";
import StatusBar from "./StatusBar";
import { useDaemonLifecycle, useDaemonStore } from "@monoco-io/kanban-core";
import ProjectTreeSelector from "./ProjectTreeSelector";
import ActivityDrawer from "./ActivityDrawer";

interface LayoutShellProps {
  children: React.ReactNode;
}

const NavItem = ({
  icon,
  path,
  label,
}: {
  icon: any;
  path: string;
  label: string;
}) => {
  const pathname = usePathname();
  const isActive = pathname === path;

  return (
    <Tooltip content={label} position={Position.RIGHT} hoverOpenDelay={0}>
      <Link href={path} className="block mb-4">
        <div
            className={`
            w-10 h-10 flex items-center justify-center rounded-xl transition-all duration-200
            ${
              isActive
                ? "bg-accent/10 text-accent border border-accent/20 shadow-[0_0_15px_rgba(59,130,246,0.3)]"
                : "text-text-muted hover:text-text-primary hover:bg-surface-highlight"
            }
          `}>
          <Icon icon={icon} size={20} />
        </div>
      </Link>
    </Tooltip>
  );
};

export default function LayoutShell({ children }: LayoutShellProps) {
  
  const { projects, currentProjectId } = useDaemonStore();
  const [isActivityOpen, setIsActivityOpen] = useState(false);
  
  const currentProject = projects?.find((p: any) => p.id === currentProjectId);

  return (
    <div className="flex flex-col h-screen w-full overflow-hidden bg-canvas text-text-primary">
      <div className="flex flex-row flex-1 w-full overflow-hidden relative">
        {/* Glass Sidebar */}
        <div className="w-16 flex flex-col items-center py-6 z-50 glass-header border-r border-border-subtle bg-surface/80">
            {/* Logo Area */}
            <div className="mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg transform hover:scale-105 transition-transform cursor-pointer">
                <span className="font-bold text-white text-lg">M</span>
            </div>
            </div>

            {/* Navigation */}
            <div className="flex-1 w-full flex flex-col items-center">
            <NavItem icon="dashboard" path="/dashboard" label="Dashboard" />
            <NavItem icon="layout-grid" path="/overview" label="Overview" />
            <NavItem icon="git-branch" path="/issues" label="Detailed" />
            <NavItem icon="cube" path="/components" label="Components" />
            </div>

            {/* Bottom Actions / Footer */}
            <div className="w-full flex flex-col items-center gap-4 pb-4">
            
            <div className="w-8 h-1 bg-border-subtle rounded-full opacity-20" />

            <NavItem icon="cog" path="/settings" label="Settings" />

            <div className="w-8 h-8 rounded-full bg-surface-highlight border border-border-subtle flex items-center justify-center overflow-hidden hover:border-accent transition-colors cursor-pointer">
                <Icon icon="user" size={14} className="text-text-muted hover:text-text-primary" />
            </div>
            </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col h-full overflow-hidden relative">
            {/* Background Grids/Effects */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
            <div className="absolute inset-0 bg-gradient-to-tr from-canvas via-transparent to-transparent pointer-events-none" />
            
            {/* Top Bar */}
            <div className="h-14 w-full flex items-center justify-between px-6 border-b border-border-subtle bg-surface/30 backdrop-blur-sm z-20 shrink-0">
                {/* Project Selector */}
                <Popover
                    content={<ProjectTreeSelector />}
                    position={Position.BOTTOM_LEFT}
                    minimal={true}
                    className="min-w-[200px]"
                >
                    <div className="flex items-center gap-2 cursor-pointer hover:bg-surface-highlight p-1.5 rounded-md transition-colors">
                        <div className={`w-6 h-6 flex items-center justify-center rounded bg-accent/10 text-accent`}>
                             <Icon icon="briefcase" size={14} />
                        </div>
                        <span className="font-semibold text-sm text-text-primary max-w-[200px] truncate">
                            {currentProject?.name || "Select Project"}
                        </span>
                        <Icon icon="chevron-down" size={12} className="text-text-muted" />
                    </div>
                </Popover>

                {/* Right Actions */}
                <div className="flex items-center gap-2">
                     <Tooltip content="Activity Feed" position={Position.BOTTOM}>
                        <Button 
                            minimal 
                            icon="notifications" 
                            onClick={() => setIsActivityOpen(true)}
                            className={isActivityOpen ? "bg-surface-highlight text-accent" : "text-text-muted"}
                        />
                     </Tooltip>
                </div>
            </div>

            <div className="relative z-0 flex-1 w-full overflow-hidden">
                {children}
            </div>
            
            <ActivityDrawer isOpen={isActivityOpen} onClose={() => setIsActivityOpen(false)} />
        </div>
      </div>
      
      <StatusBar />
    </div>
  );
}
