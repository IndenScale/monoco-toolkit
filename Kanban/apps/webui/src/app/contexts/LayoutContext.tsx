"use client";

import React, { createContext, useContext, useState, useCallback } from "react";

interface LayoutContextType {
  isActivityOpen: boolean;
  toggleActivity: () => void;
  openActivity: () => void;
  closeActivity: () => void;
}

const LayoutContext = createContext<LayoutContextType>({
  isActivityOpen: false,
  toggleActivity: () => {},
  openActivity: () => {},
  closeActivity: () => {},
});

export function LayoutProvider({ children }: { children: React.ReactNode }) {
  const [isActivityOpen, setIsActivityOpen] = useState(false);

  const toggleActivity = useCallback(
    () => setIsActivityOpen((prev) => !prev),
    []
  );
  const openActivity = useCallback(() => setIsActivityOpen(true), []);
  const closeActivity = useCallback(() => setIsActivityOpen(false), []);

  return (
    <LayoutContext.Provider
      value={{
        isActivityOpen,
        toggleActivity,
        openActivity,
        closeActivity,
      }}>
      {children}
    </LayoutContext.Provider>
  );
}

export const useLayout = () => useContext(LayoutContext);
