"use client";

import React, { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { useTerminal } from "@/app/contexts/TerminalContext";

interface XTermViewProps {
  sessionId: string;
  initialCwd?: string;
  onClose?: () => void;
  className?: string;
  themeMode?: "light" | "dark";
}

const getTheme = (mode: "light" | "dark" = "dark") => {
  if (mode === "light") {
    // Light Theme (Paper Color)
    return {
      background: "#ffffff",
      foreground: "#333333",
      cursor: "#333333",
      selectionBackground: "rgba(0, 0, 0, 0.1)",
      cursorAccent: "#ffffff",
    };
  } else {
    // Dark Theme (VS Code Dark)
    return {
      background: "#1e1e1e", // or use CSS var via getComputedStyle?
      // Xterm requires hex usually.
      // Stick to a balanced dark gray matching shadcn card or background.
      // Shadcn slate-950 is #020617. Let's use #0f172a (slate-900) or pure #000.
      // Let's stick to standard VSCode-like for now as it maps well to editors.
      foreground: "#cccccc",
      cursor: "#ffffff",
      selectionBackground: "rgba(255, 255, 255, 0.3)",
      cursorAccent: "#000000",
    };
  }
};

/* ... */

const XTermComponent = ({
  sessionId,
  initialCwd,
  onClose,
  className = "",
  themeMode = "dark",
}: XTermViewProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<any>(null);
  const fitAddonRef = useRef<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const { setAgentStatus, reconnectKey } = useTerminal();

  // Retry logic state
  const retryCount = useRef(0);
  const maxRetries = 10;
  const isUnmounting = useRef(false);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Update theme when themeMode changes
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.options.theme = getTheme(themeMode);
    }
  }, [themeMode]);

  useEffect(() => {
    if (!containerRef.current) return;

    isUnmounting.current = false;

    let term: any;
    let fitAddon: any;
    let webLinksAddon: any;
    let disposable: any;
    let resizeObserver: ResizeObserver | null = null;

    const initTerminal = async () => {
      const { Terminal } = await import("@xterm/xterm");
      const { FitAddon } = await import("@xterm/addon-fit");
      const { WebLinksAddon } = await import("@xterm/addon-web-links");

      term = new Terminal({
        cursorBlink: true,
        fontSize: 13,
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        theme: getTheme(themeMode),
        allowProposedApi: true,
      });

      fitAddon = new FitAddon();
      webLinksAddon = new WebLinksAddon();

      term.loadAddon(fitAddon);
      term.loadAddon(webLinksAddon);

      term.open(containerRef.current!);
      fitAddon.fit();

      terminalRef.current = term;
      fitAddonRef.current = fitAddon;

      // Connect Function
      const connect = () => {
        if (isUnmounting.current) return;

        const currentCols = term.cols;
        const currentRows = term.rows;

        // Avoid connecting with invalid/zero dimensions
        if (currentCols <= 1 || currentRows <= 1) {
          console.warn("PTY: Skipping connect due to small window size", {
            currentCols,
            currentRows,
          });
          return;
        }

        const wsUrl = new URL(`ws://127.0.0.1:3124/api/v1/pty/ws/${sessionId}`);
        if (initialCwd) {
          wsUrl.searchParams.append("cwd", initialCwd);
        }
        wsUrl.searchParams.append("cols", String(currentCols));
        wsUrl.searchParams.append("rows", String(currentRows));

        console.log(`Connecting to PTY: ${wsUrl.toString()}`);
        setAgentStatus("connecting");

        const ws = new WebSocket(wsUrl.toString());
        ws.binaryType = "arraybuffer";

        ws.onopen = () => {
          if (isUnmounting.current) {
            if (ws.readyState === WebSocket.OPEN) ws.close();
            return;
          }
          console.log("PTY Connected");
          setConnected(true);
          setAgentStatus("connected");
          retryCount.current = 0; // Reset retry count on successful connection

          // Initial resize to sync dimensions
          if (fitAddonRef.current) {
            fitAddonRef.current.fit();
          }
        };

        ws.onclose = (ev) => {
          if (isUnmounting.current) return;

          console.log("PTY Disconnected", ev.code, ev.reason);
          setConnected(false);
          setAgentStatus("disconnected");

          // Retry logic
          if (retryCount.current < maxRetries) {
            const timeout = Math.min(
              1000 * Math.pow(1.5, retryCount.current),
              10000
            );
            console.log(
              `Reconnecting in ${timeout}ms (Attempt ${
                retryCount.current + 1
              }/${maxRetries})...`
            );
            retryCount.current++;
            reconnectTimeoutRef.current = setTimeout(connect, timeout);
          } else {
            console.error("Max retries reached. PTY connection failed.");
            if (onClose) onClose();
          }
        };

        ws.onerror = (err) => {
          console.error("PTY Error", err);
          // onclose will be called after onerror, so retry logic is handled there
        };

        ws.onmessage = (ev: MessageEvent) => {
          if (typeof ev.data === "string") {
            term.write(ev.data);
          } else {
            term.write(new Uint8Array(ev.data));
          }
        };

        wsRef.current = ws;
      };

      // Start connection
      connect();

      // 3. Handle Input (xterm -> PTY)
      // Use wsRef.current to always get the latest WebSocket instance
      disposable = term.onData((data: string) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(data);
        }
      });

      // 4. Handle Resize with ResizeObserver
      const handleResize = () => {
        if (!fitAddonRef.current) return;

        try {
          fitAddonRef.current.fit();
          const { cols, rows } = terminalRef.current!;

          // Lazy connect if we skipped it initially
          if (!wsRef.current && !isUnmounting.current && cols > 1 && rows > 1) {
            connect();
            return;
          }

          if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN)
            return;

          const resizeCmd = JSON.stringify({
            type: "resize",
            cols,
            rows,
          });
          wsRef.current.send(resizeCmd);
        } catch (e) {
          console.error("Resize error:", e);
        }
      };

      resizeObserver = new ResizeObserver(() => {
        handleResize();
      });

      if (containerRef.current && resizeObserver) {
        resizeObserver.observe(containerRef.current);
      }

      // Initial fit
      setTimeout(() => handleResize(), 100);
    };

    initTerminal();

    return () => {
      isUnmounting.current = true;
      if (reconnectTimeoutRef.current)
        clearTimeout(reconnectTimeoutRef.current);
      if (disposable) disposable.dispose();
      if (term) term.dispose();
      if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) {
        wsRef.current.close();
      }
      if (resizeObserver) resizeObserver.disconnect();
    };
  }, [sessionId, initialCwd, onClose, reconnectKey]); // Intentional: themeMode not here to avoid re-init

  const handleContainerClick = () => {
    if (terminalRef.current) {
      terminalRef.current.focus();
    }
  };

  return (
    <div
      className={`w-full h-full ${className}`}
      style={{ backgroundColor: getTheme(themeMode).background }}
      onClick={handleContainerClick}>
      <div ref={containerRef} className="w-full h-full px-2 py-1" />
    </div>
  );
};

export const XTermView = dynamic(() => Promise.resolve(XTermComponent), {
  ssr: false,
});
