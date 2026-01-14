"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { useTerminal } from "@/app/contexts/TerminalContext";
import { XTermView } from "./XTermView";
import { ChevronUp, ChevronDown, GripHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/components/theme-provider";

export const TerminalPanel: React.FC = () => {
  const { isOpen, toggle, activeSessionId } = useTerminal();
  const [height, setHeight] = useState(320); // Default height
  const [isResizing, setIsResizing] = useState(false);
  const { theme } = useTheme();
  const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark">("dark");

  // Persistence for Height
  useEffect(() => {
    const savedHeight = localStorage.getItem("monoco_terminal_height");
    if (savedHeight) {
      setHeight(Number(savedHeight));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("monoco_terminal_height", String(height));
  }, [height]);

  useEffect(() => {
    // Resolve theme (system -> light/dark)
    const resolve = () => {
      if (theme === "system") {
        const isDark = window.matchMedia(
          "(prefers-color-scheme: dark)"
        ).matches;
        setResolvedTheme(isDark ? "dark" : "light");
      } else {
        setResolvedTheme(theme as "light" | "dark");
      }
    };
    resolve();

    // If system, listen for changes?
    // The ThemeProvider handles DOM class updates, but here we need state for XTerm.
    if (theme === "system") {
      const media = window.matchMedia("(prefers-color-scheme: dark)");
      const listener = () => resolve();
      media.addEventListener("change", listener);
      return () => media.removeEventListener("change", listener);
    }
  }, [theme]);

  // Constraints
  const MIN_HEIGHT = 150;
  const MAX_HEIGHT = 800;

  // Handle Resize
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent text selection
    setIsResizing(true);
  };

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const offset = 24; // StatusBar height
      const newHeight = window.innerHeight - e.clientY - offset;

      if (newHeight >= MIN_HEIGHT && newHeight <= MAX_HEIGHT) {
        setHeight(newHeight);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing]);

  // Keyboard Resize: Cmd + J + Up/Down
  const CHARACTER_HEIGHT = 19;
  const keysPressed = useRef<{ [key: string]: boolean }>({});

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      keysPressed.current[e.key.toLowerCase()] = true;

      if (e.metaKey && keysPressed.current["j"]) {
        if (e.key === "ArrowUp") {
          e.preventDefault();
          e.stopPropagation();
          setHeight((h) => Math.min(h + CHARACTER_HEIGHT, MAX_HEIGHT));
        } else if (e.key === "ArrowDown") {
          e.preventDefault();
          e.stopPropagation();
          setHeight((h) => Math.max(h - CHARACTER_HEIGHT, MIN_HEIGHT));
        }
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      keysPressed.current[e.key.toLowerCase()] = false;
    };

    window.addEventListener("keydown", handleKeyDown, true); // Capture phase to prevent toggle if possible
    window.addEventListener("keyup", handleKeyUp, true);
    return () => {
      window.removeEventListener("keydown", handleKeyDown, true);
      window.removeEventListener("keyup", handleKeyUp, true);
    };
  }, []);

  // Use CSS variables for colors, derived from theme
  // We don't need to manually pass colors if we use Tailwind classes correctly,
  // BUT XTerm needs explicit hex values. We'll handle that in XTermView or pass a prop.

  return (
    <>
      {/* Resizing Overlay to capture loose mouse events and enforce cursor */}
      {isResizing && (
        <div
          className="fixed inset-0 z-[100] cursor-ns-resize bg-transparent"
          style={{ userSelect: "none" }}
        />
      )}

      {/* The Panel */}
      <div
        className={cn(
          "relative z-40 flex flex-col shadow-[0_-5px_20px_rgba(0,0,0,0.1)] transition-all duration-200 ease-in-out bg-card border-t border-border",
          // Only animate translation/opacity when NOT resizing to keep it snappy.
          // Actually, keep transition but maybe disable it during resize if specific perf needed.
          // For now, let's keep it simple.
          isOpen ? "translate-y-0 opacity-100" : "translate-y-[120%] opacity-0"
        )}
        style={{
          height: isOpen ? height : 0,
          // Position absolute within the content area to respect sidebar width
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          transitionProperty: isResizing ? "none" : "all", // Disable transition during drag for direct feedback
        }}>
        {/* Resize Handle / Header */}
        <div
          className="h-2 w-full cursor-ns-resize flex items-center justify-center bg-muted/30 hover:bg-accent/50 transition-colors border-b border-border/50 group"
          onMouseDown={handleMouseDown}>
          <div className="w-16 h-1 rounded-full bg-border group-hover:bg-primary/50 transition-colors" />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden bg-background">
          <XTermView
            sessionId={activeSessionId}
            themeMode={resolvedTheme as "light" | "dark"}
          />
        </div>
      </div>
    </>
  );
};
