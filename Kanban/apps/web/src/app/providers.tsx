"use client";

import {
  useDaemonLifecycle,
  useSSEConnection,
  useKanbanSync,
  useDaemonStore,
} from "@monoco/kanban-core";
import { loader } from "@monaco-editor/react";
import { useEffect } from "react";
import { TermProvider } from "./contexts/TermContext";

export function Providers({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Configure Monaco Editor to use local installation instead of CDN
    // Dynamic import to avoid server-side "window is not defined" error
    import("monaco-editor").then((monaco) => {
      loader.config({ monaco });

      // Define MonacoEnvironment to point to local workers
      // @ts-ignore
      window.MonacoEnvironment = {
        getWorkerUrl: function (moduleId: any, label: string) {
          if (label === "json") {
            return "/monaco-editor/min/vs/json.worker.js";
          }
          if (label === "css" || label === "scss" || label === "less") {
            return "/monaco-editor/min/vs/css.worker.js";
          }
          if (label === "html" || label === "handlebars" || label === "razor") {
            return "/monaco-editor/min/vs/html.worker.js";
          }
          if (label === "typescript" || label === "javascript") {
            return "/monaco-editor/min/vs/ts.worker.js";
          }
          return "/monaco-editor/min/vs/editor.worker.js";
        },
      };
    });
  }, []);

  // Initialize Daemon Connection Lifecycle (Polling/Backoff)
  useDaemonLifecycle();

  // Initialize SSE Connection (Data Stream)
  useSSEConnection();

  // Initialize Kanban Data Sync (Store Updates)
  useKanbanSync();

  return (
    <TermProvider>
      {children}
    </TermProvider>
  );
}
