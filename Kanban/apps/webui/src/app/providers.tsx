"use client";

import {
  useDaemonLifecycle,
  useSSEConnection,
  useKanbanSync,
  useDaemonStore,
} from "@monoco-io/kanban-core";
import { loader } from "@monaco-editor/react";
import { useEffect } from "react";
import { LayoutProvider } from "./contexts/LayoutContext";
import { BridgeProvider } from "./contexts/BridgeContext";

export function Providers({ children }: { children: React.ReactNode }) {
  /* ... existing monaco config ... */
  useEffect(() => {
    loader.config({
      paths: {
        vs: "/monaco-editor/min/vs",
      },
    });

    // @ts-ignore
    window.MonacoEnvironment = {
      getWorkerUrl: function (moduleId: any, label: string) {
        if (label === "json") return "/monaco-editor/min/vs/json.worker.js";
        if (label === "css" || label === "scss" || label === "less")
          return "/monaco-editor/min/vs/css.worker.js";
        if (label === "html" || label === "handlebars" || label === "razor")
          return "/monaco-editor/min/vs/html.worker.js";
        if (label === "typescript" || label === "javascript")
          return "/monaco-editor/min/vs/ts.worker.js";
        return "/monaco-editor/min/vs/editor.worker.js";
      },
    };
  }, []);

  useDaemonLifecycle();
  useSSEConnection();
  useKanbanSync();

  return (
    <BridgeProvider>
      <LayoutProvider>{children}</LayoutProvider>
    </BridgeProvider>
  );
}
