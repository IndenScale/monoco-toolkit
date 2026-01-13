"use client";

import * as React from "react";

export type Theme = "dark" | "light" | "system";

type ThemeProviderProps = {
  children: React.ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
};

type ThemeProviderState = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
};

const ThemeProviderContext = React.createContext<ThemeProviderState>({
  theme: "system",
  setTheme: () => null,
});

export function ThemeProvider({
  children,
  defaultTheme = "system",
  storageKey = "monoco-ui-theme",
  ...props
}: ThemeProviderProps) {
  // Initialize with defaultTheme to avoid hydration mismatch (server vs client)
  const [theme, setTheme] = React.useState<Theme>(defaultTheme);
  const [mounted, setMounted] = React.useState(false);

  // Initial load from storage
  React.useEffect(() => {
    setMounted(true);
    try {
      const storedTheme = localStorage.getItem(storageKey) as Theme;
      if (storedTheme) {
        setTheme(storedTheme);
      }
    } catch (e) {
      console.warn("Failed to access localStorage", e);
    }
  }, [storageKey]);

  // Apply theme to DOM
  React.useEffect(() => {
    if (!mounted) return; // Wait for mount

    const root = window.document.documentElement;
    const body = window.document.body;

    root.classList.remove("light", "dark");
    body.classList.remove("bp6-dark");

    const applyTheme = (t: Theme) => {
      let activeTheme = t;
      if (t === "system") {
        activeTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";
      }

      root.classList.add(activeTheme);
      root.style.colorScheme = activeTheme; // Help browser UI

      if (activeTheme === "dark") {
        body.classList.add("bp6-dark");
      }
    };

    applyTheme(theme);

    // Listen for system changes if system theme
    if (theme === "system") {
      const media = window.matchMedia("(prefers-color-scheme: dark)");
      const listener = () => {
        // Re-apply
        root.classList.remove("light", "dark");
        body.classList.remove("bp6-dark");
        applyTheme("system");
      };
      media.addListener(listener);
      return () => media.removeListener(listener);
    }
  }, [theme, mounted]);

  const value = {
    theme,
    setTheme: (newTheme: Theme) => {
      try {
        localStorage.setItem(storageKey, newTheme);
      } catch (e) {
        console.warn("Failed to write localStorage", e);
      }
      setTheme(newTheme);
    },
  };

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  );
}

export const useTheme = () => {
  const context = React.useContext(ThemeProviderContext);

  if (context === undefined)
    throw new Error("useTheme must be used within a ThemeProvider");

  return context;
};
