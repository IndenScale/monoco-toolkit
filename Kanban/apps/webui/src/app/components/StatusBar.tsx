import React from "react";
import { Icon, Spinner, Intent, Tooltip } from "@blueprintjs/core";
import { useDaemonStore } from "@monoco-io/kanban-core";

import { useLayout } from "../contexts/LayoutContext";
import { ChevronUp, ChevronDown, RotateCcw, Bell } from "lucide-react";

export default function StatusBar() {
  const { status, daemonUrl, checkConnection } = useDaemonStore();

  const { toggleActivity } = useLayout();

  const getStatusColor = () => {
    switch (status) {
      case "connected":
        return "bg-emerald-500";
      case "connecting":
        return "bg-yellow-500";
      case "error":
        return "bg-red-500";
      default:
        return "bg-slate-500";
    }
  };

  const getStatusText = () => {
    switch (status) {
      case "connected":
        return "Connected";
      case "connecting":
        return "Connecting...";
      default:
        return "Disconnected";
    }
  };

  return (
    <footer className="h-6 bg-surface-highlight border-t border-border-subtle flex items-center px-3 text-[11px] text-text-muted select-none z-50 shrink-0 justify-between">
      <div className="flex items-center gap-4">
        <Tooltip
          content={
            <div className="text-[10px] p-0.5">
              <div className="font-bold opacity-80 uppercase mb-1">
                Daemon Connection
              </div>
              <div>
                Server:{" "}
                <span className="text-blue-400">{daemonUrl || "Not Set"}</span>
              </div>
              <div className="mt-1 opacity-50 italic">
                Click to force re-check
              </div>
            </div>
          }
          hoverOpenDelay={300}>
          <div
            className="flex items-center gap-2 hover:bg-white/5 px-2 py-0.5 rounded cursor-pointer transition-colors group"
            onClick={() => checkConnection()}>
            <div
              className={`w-2 h-2 rounded-full transition-shadow ${getStatusColor()} ${
                status !== "connected" ? "animate-pulse" : ""
              } group-hover:shadow-[0_0_5px_rgba(255,255,255,0.5)]`}
            />
            <span>{getStatusText()}</span>
          </div>
        </Tooltip>

        <div className="flex items-center gap-1 hover:bg-white/5 px-2 py-0.5 rounded cursor-pointer transition-colors">
          <Icon icon="git-branch" size={12} />
          <span>main</span>
        </div>

        <div className="flex items-center gap-1 hover:bg-white/5 px-2 py-0.5 rounded cursor-pointer transition-colors">
          <Icon icon="error" size={12} className="text-text-muted" />
          <span>0</span>
          <Icon icon="warning-sign" size={12} className="text-text-muted" />
          <span>0</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1 hover:bg-white/5 px-2 py-0.5 rounded cursor-pointer transition-colors">
          <span className="text-text-muted">UTF-8</span>
        </div>
        <Tooltip content="Activity Feed" hoverOpenDelay={300}>
          <div
            className="flex items-center gap-1 hover:bg-white/10 px-2 py-0.5 rounded cursor-pointer transition-colors text-text-muted hover:text-text-primary"
            onClick={toggleActivity}>
            <Bell size={12} />
          </div>
        </Tooltip>
      </div>
    </footer>
  );
}
