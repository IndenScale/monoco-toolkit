"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";

interface TerminalContextType {
  isOpen: boolean;
  toggle: () => void;
  open: () => void;
  close: () => void;
  activeSessionId: string;
  setActiveSessionId: (id: string) => void;
  agentStatus: "connected" | "disconnected" | "connecting";
  setAgentStatus: (status: "connected" | "disconnected" | "connecting") => void;
  reconnect: () => void;
  reconnectKey: number;
}

const TerminalContext = createContext<TerminalContextType>({
  isOpen: false,
  toggle: () => {},
  open: () => {},
  close: () => {},
  activeSessionId: "main",
  setActiveSessionId: () => {},
  agentStatus: "disconnected",
  setAgentStatus: () => {},
  reconnect: () => {},
  reconnectKey: 0,
});

export function TerminalProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState("main");

  // Persistence: Load from localStorage on mount
  useEffect(() => {
    const savedIsOpen = localStorage.getItem("monoco_terminal_isOpen");
    if (savedIsOpen) {
      setIsOpen(savedIsOpen === "true");
    }
    const savedSessionId = localStorage.getItem("monoco_terminal_sessionId");
    if (savedSessionId) {
      setActiveSessionId(savedSessionId);
    }
  }, []);

  // Persistence: Save to localStorage on change
  useEffect(() => {
    localStorage.setItem("monoco_terminal_isOpen", String(isOpen));
  }, [isOpen]);

  useEffect(() => {
    localStorage.setItem("monoco_terminal_sessionId", activeSessionId);
  }, [activeSessionId]);

  const [agentStatus, setAgentStatus] = useState<
    "connected" | "disconnected" | "connecting"
  >("disconnected");
  const [reconnectKey, setReconnectKey] = useState(0);

  const toggle = useCallback(() => setIsOpen((prev) => !prev), []);
  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const reconnect = useCallback(() => setReconnectKey((prev) => prev + 1), []);

  // Global Shortcut: Cmd+J (or Ctrl+J) to toggle
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "j") {
        e.preventDefault();
        toggle();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [toggle]);

  return (
    <TerminalContext.Provider
      value={{
        isOpen,
        toggle,
        open,
        close,
        activeSessionId,
        setActiveSessionId,
        agentStatus,
        setAgentStatus,
        reconnect,
        reconnectKey,
      }}>
      {children}
    </TerminalContext.Provider>
  );
}

export const useTerminal = () => useContext(TerminalContext);
