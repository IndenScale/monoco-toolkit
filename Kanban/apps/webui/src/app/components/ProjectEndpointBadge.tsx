"use client";

import { useState, useEffect } from "react";
import { useDaemonStore } from "@monoco/kanban-core";
import { Tag, Popover, InputGroup, Button, Intent } from "@blueprintjs/core";

export default function ProjectEndpointBadge() {
  const { daemonUrl, setDaemonUrl, status, info } = useDaemonStore();
  const [isOpen, setIsOpen] = useState(false);
  const [inputUrl, setInputUrl] = useState(daemonUrl);

  // Sync input with store updates
  useEffect(() => {
    setInputUrl(daemonUrl);
  }, [daemonUrl]);

  const handleSave = () => {
    setDaemonUrl(inputUrl);
    setIsOpen(false);
  };

  const getStatusIntent = (): Intent => {
    switch (status) {
      case "connected":
        return Intent.SUCCESS;
      case "connecting":
        return Intent.WARNING;
      case "error":
        return Intent.DANGER;
      default:
        return Intent.NONE;
    }
  };

  const statusText = () => {
    if (status === "connected") {
      return info?.name ? `Daemon: ${info.name}` : "Daemon Online";
    }
    if (status === "connecting") return "Connecting...";
    if (status === "error") return "Connection Failed";
    return "Disconnected";
  };

  return (
    <Popover
      isOpen={isOpen}
      onInteraction={(nextOpenState) => setIsOpen(nextOpenState)}
      placement="right"
      content={
        <div className="p-4 w-80 bg-surface border border-border-subtle rounded-lg shadow-xl backdrop-blur-md">
          <h4 className="mb-3 font-bold text-sm text-text-primary">
            Daemon Configuration
          </h4>
          <div className="mb-3">
            <label className="text-xs text-text-muted mb-1 block">
              Endpoint URL
            </label>
            <InputGroup
              className="bp5-dark"
              value={inputUrl}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setInputUrl(e.target.value)
              }
              placeholder="http://127.0.0.1:8642"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button
              small
              text="Cancel"
              minimal
              className="!text-text-muted hover:!text-text-primary"
              onClick={() => setIsOpen(false)}
            />
            <Button
              small
              text="Update & Connect"
              intent={Intent.PRIMARY}
              onClick={handleSave}
            />
          </div>
        </div>
      }>
      <Tag
        interactive
        intent={getStatusIntent()}
        minimal
        icon={status === "connected" ? "feed" : "offline"}
        className="cursor-pointer !bg-surface-highlight hover:!bg-surface !text-text-primary !border-border-subtle"
        title={daemonUrl}>
        {statusText()}
      </Tag>
    </Popover>
  );
}
