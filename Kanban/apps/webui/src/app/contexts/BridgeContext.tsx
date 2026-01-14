"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { vscodeMessenger } from "@monoco-io/kanban-core";

interface BridgeContextType {
  isVsCode: boolean;
  postMessage: (type: string, payload?: any) => void;
  lastMessage: any;
}

const BridgeContext = createContext<BridgeContextType | undefined>(undefined);

export function BridgeProvider({ children }: { children: React.ReactNode }) {
  const [lastMessage, setLastMessage] = useState<any>(null);

  useEffect(() => {
    if (vscodeMessenger.isVsCode) {
      console.log("[Bridge] Detected VS Code environment");

      const unsub = vscodeMessenger.onMessage("COMMAND", (msg) => {
        console.log("[Bridge] Received COMMAND from extension:", msg);
        setLastMessage(msg);
      });

      // Notify extension that webview is ready
      vscodeMessenger.postMessage("WEBVIEW_READY");

      return unsub;
    }
  }, []);

  const value = {
    isVsCode: vscodeMessenger.isVsCode,
    postMessage: (type: string, payload?: any) =>
      vscodeMessenger.postMessage(type, payload),
    lastMessage,
  };

  return (
    <BridgeContext.Provider value={value}>{children}</BridgeContext.Provider>
  );
}

export function useBridge() {
  const context = useContext(BridgeContext);
  if (context === undefined) {
    throw new Error("useBridge must be used within a BridgeProvider");
  }
  return context;
}
