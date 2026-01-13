"use client";

import React, { useEffect, useState } from "react";
import {
  Card,
  Elevation,
  Switch,
  Button,
  FormGroup,
  InputGroup,
  Intent,
  Tag,
} from "@blueprintjs/core";
import { useTheme } from "../../components/theme-provider";
import { useDaemonStore } from "@monoco-io/kanban-core";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { daemonUrl, setDaemonUrl, status, checkConnection } = useDaemonStore();
  const [urlInput, setUrlInput] = useState(daemonUrl);
  const [isClient, setIsClient] = useState(false);

  // Hydration fix
  useEffect(() => {
    setIsClient(true);
    setUrlInput(daemonUrl);
  }, [daemonUrl]);

  const handleSaveUrl = () => {
    if (urlInput !== daemonUrl) {
      setDaemonUrl(urlInput);
    } else {
      checkConnection();
    }
  };

  const statusIntent =
    status === "connected"
      ? Intent.SUCCESS
      : status === "connecting"
      ? Intent.WARNING
      : Intent.DANGER;

  if (!isClient) return null;

  return (
    <main className="h-full flex flex-col font-sans overflow-hidden bg-canvas">
      <header className="px-6 py-6 shrink-0 z-10 border-b border-border-subtle bg-surface/50 backdrop-blur-sm">
        <h1 className="text-2xl font-bold text-text-primary tracking-tight mb-1">
          Settings
        </h1>
        <p className="text-sm text-text-muted">
          Manage your preferences and project configurations.
        </p>
      </header>

      <div className="flex-1 overflow-auto px-6 py-6">
        <div className="max-w-3xl space-y-6">
          <Card elevation={Elevation.ONE}>
            <h3 className="text-lg font-semibold mb-4 text-text-primary">
              Appearance
            </h3>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h5 className="font-medium text-text-primary">Dark Mode</h5>
                <p className="text-sm text-text-muted">
                  Use dark theme for the interface.
                </p>
              </div>
              <Switch
                checked={theme === "dark"}
                onChange={() => setTheme(theme === "dark" ? "light" : "dark")}
                labelElement={<span className="ml-2">{theme}</span>}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <h5 className="font-medium text-text-primary">Compact View</h5>
                <p className="text-sm text-text-muted">
                  Show more content on the screen.
                </p>
              </div>
              <Switch disabled label="Coming soon" />
            </div>
          </Card>

          <Card elevation={Elevation.ONE}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">
                Connection
              </h3>
              <Tag intent={statusIntent} minimal className="uppercase">
                {status}
              </Tag>
            </div>

            <FormGroup
              label="Daemon URL"
              labelInfo="(required)"
              helperText="The URL where the Monoco background daemon is running.">
              <InputGroup
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="http://127.0.0.1:8642"
                rightElement={
                  <Button
                    minimal
                    icon="refresh"
                    onClick={() => setUrlInput("http://127.0.0.1:8642")}
                  />
                }
              />
            </FormGroup>
            <div className="flex gap-2">
              <Button
                intent={Intent.PRIMARY}
                text="Save & Connect"
                onClick={handleSaveUrl}
                loading={status === "connecting"}
              />
              <Button
                icon="refresh"
                text="Retry API"
                onClick={() => checkConnection()}
              />
            </div>

            {status === "error" && (
              <div className="mt-4 p-3 bg-red-500/10 text-red-500 rounded text-sm">
                Failed to communicate with daemon. Please check if the server is
                running and the URL is correct. If the server is running on a
                dynamic port, verify the port number from logs.
              </div>
            )}
          </Card>

          <Card elevation={Elevation.ONE}>
            <h3 className="text-lg font-semibold mb-4 text-text-primary">
              About
            </h3>
            <p className="text-text-muted mb-2">
              Monoco Premium Cockpit v0.1.0
            </p>
            <p className="text-text-muted text-sm">Running on local daemon.</p>
          </Card>
        </div>
      </div>
    </main>
  );
}
