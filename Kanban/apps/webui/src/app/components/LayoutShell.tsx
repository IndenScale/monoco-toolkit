"use client";

import React from "react";
import { useLayout } from "../contexts/LayoutContext";
import { usePathname } from "next/navigation";
import Link from "next/link";
import StatusBar from "./StatusBar";
import { useDaemonStore } from "@monoco-io/kanban-core";
import ProjectTreeSelector from "./ProjectTreeSelector";
import ActivityDrawer from "./ActivityDrawer";
import {
  LayoutDashboard,
  Grid,
  GitBranch,
  Box,
  Settings,
  User,
  Briefcase,
  ChevronDown,
  Bell,
  ExternalLink,
} from "lucide-react";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface LayoutShellProps {
  children: React.ReactNode;
}

const NavItem = ({
  icon: Icon,
  path,
  label,
}: {
  icon: React.ComponentType<{ size?: number | string; className?: string }>;
  path: string;
  label: string;
}) => {
  const pathname = usePathname();
  const isActive = pathname === path;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Link href={path} className="block mb-4">
          <div
            className={`
            w-10 h-10 flex items-center justify-center rounded-xl transition-all duration-200
            ${
              isActive
                ? "bg-blue-600 text-white shadow-[0_0_15px_rgba(59,130,246,0.5)]"
                : "text-text-muted hover:text-text-primary hover:bg-surface-highlight"
            }
          `}>
            <Icon size={20} />
          </div>
        </Link>
      </TooltipTrigger>
      <TooltipContent side="right">
        <p>{label}</p>
      </TooltipContent>
    </Tooltip>
  );
};

import { useBridge } from "../contexts/BridgeContext";
import "../vscode-theme.css";

// ... existing NavItem component ...

export default function LayoutShell({ children }: LayoutShellProps) {
  const { projects, currentProjectId } = useDaemonStore();
  const { isActivityOpen, closeActivity } = useLayout();
  const { isVsCode, postMessage } = useBridge();

  const currentProject = projects?.find((p: any) => p.id === currentProjectId);

  return (
    <div
      className={`flex flex-col h-screen w-full overflow-hidden bg-canvas text-text-primary ${
        isVsCode ? "vscode-mode" : ""
      }`}>
      <div className="flex flex-row flex-1 w-full overflow-hidden relative">
        {/* Glass Sidebar - Hidden in VS Code Mode */}
        {!isVsCode && (
          <div className="w-16 flex flex-col items-center py-6 z-50 glass-header border-r border-border-subtle bg-surface/80">
            {/* Logo Area */}
            <div className="mb-8">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg transform hover:scale-105 transition-transform cursor-pointer">
                <span className="font-bold text-white text-lg">M</span>
              </div>
            </div>

            {/* Navigation */}
            <TooltipProvider delayDuration={0}>
              <div className="flex-1 w-full flex flex-col items-center gap-4">
                <NavItem
                  icon={LayoutDashboard}
                  path="/dashboard"
                  label="Dashboard"
                />
                <NavItem icon={Grid} path="/overview" label="Overview" />
                <NavItem icon={GitBranch} path="/issues" label="Detailed" />
                <NavItem icon={Box} path="/components" label="Components" />
              </div>

              {/* Bottom Actions / Footer */}
              <div className="w-full flex flex-col items-center gap-4 pb-4">
                <div className="w-8 h-1 bg-border-subtle rounded-full opacity-20" />

                <NavItem icon={Settings} path="/settings" label="Settings" />

                <div className="w-8 h-8 rounded-full bg-surface-highlight border border-border-subtle flex items-center justify-center overflow-hidden hover:border-accent transition-colors cursor-pointer">
                  <Avatar className="h-7 w-7">
                    <AvatarImage src="" />
                    <AvatarFallback>
                      <User
                        size={14}
                        className="text-text-muted hover:text-text-primary"
                      />
                    </AvatarFallback>
                  </Avatar>
                </div>
              </div>
            </TooltipProvider>
          </div>
        )}

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col h-full overflow-hidden relative">
          {/* Background Grids/Effects - Simplified in VS Code */}
          {!isVsCode && (
            <>
              <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
              <div className="absolute inset-0 bg-gradient-to-tr from-canvas via-transparent to-transparent pointer-events-none" />
            </>
          )}

          {/* Top Bar */}

          <div className="relative z-0 flex-1 w-full overflow-hidden">
            {children}
          </div>

          <ActivityDrawer isOpen={isActivityOpen} onClose={closeActivity} />
        </div>
      </div>

      <StatusBar />

      {/* VS Code Bottom Nav */}
      {isVsCode && (
        <div className="flex flex-row justify-around items-center p-2 border-t border-border-subtle bg-surface/90 backdrop-blur-sm z-50">
          <Link href="/dashboard" className="p-2" title="Dashboard">
            <LayoutDashboard size={18} />
          </Link>
          <Link href="/overview" className="p-2" title="Overview">
            <Grid size={18} />
          </Link>
          <Link href="/issues" className="p-2" title="Detailed">
            <GitBranch size={18} />
          </Link>
          <button
            className="p-2 text-text-primary hover:text-accent transition-colors"
            title="Open in Browser"
            onClick={() => {
              postMessage("OPEN_EXTERNAL", { url: window.location.href });
            }}>
            <ExternalLink size={18} />
          </button>
        </div>
      )}
    </div>
  );
}
