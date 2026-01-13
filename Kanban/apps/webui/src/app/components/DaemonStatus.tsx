"use client";

import { useDaemonStore } from "@monoco-io/kanban-core";
import { Tag, Spinner } from "@blueprintjs/core";

export default function DaemonStatus() {
  const { status, info } = useDaemonStore();

  const getStatusProps = () => {
    switch (status) {
      case "connected":
        return {
          intent: "success" as const,
          icon: "tick-circle" as const,
          text: info?.head ? `HEAD: ${info.head.slice(0, 7)}` : "Connected",
        };
      case "connecting":
        return {
          intent: "warning" as const,
          icon: undefined,
          text: "Connecting...",
        };
      case "error":
        return {
          intent: "danger" as const,
          icon: "error" as const,
          text: "Daemon Offline",
        };
      case "disconnected":
      default:
        return {
          intent: "none" as const,
          icon: "offline" as const,
          text: "Disconnected",
        };
    }
  };

  const { intent, icon, text } = getStatusProps();

  return (
    <div className="flex items-center gap-2">
      <Tag intent={intent} icon={icon} minimal>
        {status === "connecting" && (
          <Spinner size={16} className="mr-2 inline-block" />
        )}
        {text}
      </Tag>
    </div>
  );
}
