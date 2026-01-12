import React from "react";
import { Icon, Spinner, Intent } from "@blueprintjs/core";
import { useDaemonStore } from "@monoco/kanban-core";

export default function StatusBar() {
  const { status, daemonUrl } = useDaemonStore();

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
        return `Connected to ${daemonUrl}`;
      case "connecting":
        return "Connecting to Daemon...";
      case "error":
        return "Connection Error";
      default:
        return "Disconnected";
    }
  };

  return (
    <footer className="h-6 bg-surface-highlight border-t border-border-subtle flex items-center px-3 text-[11px] text-text-muted select-none z-50 shrink-0 justify-between">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 hover:bg-white/5 px-2 py-0.5 rounded cursor-pointer transition-colors">
          <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
          <span>{getStatusText()}</span>
        </div>
        
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
         <div className="flex items-center gap-1 hover:bg-white/5 px-2 py-0.5 rounded cursor-pointer transition-colors">
             <Icon icon="notifications" size={12} />
         </div>
      </div>
    </footer>
  );
}
