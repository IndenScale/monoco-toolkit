"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useDaemonStore } from "@monoco-io/kanban-core";

type TermDictionary = Record<string, string>;

interface TermContextType {
  terms: TermDictionary;
  t: (key: string, defaultVal?: string) => string;
}

const TermContext = createContext<TermContextType>({
  terms: {},
  t: (k, d) => d || k,
});

export function TermProvider({ children }: { children: React.ReactNode }) {
  const [terms, setTerms] = useState<TermDictionary>({});
  const { daemonUrl, currentProjectId, status } = useDaemonStore();

  useEffect(() => {
    if (status !== "connected") return;

    const fetchTerms = async () => {
      try {
        const params = currentProjectId
          ? `?project_id=${currentProjectId}`
          : "";
        const res = await fetch(
          `${daemonUrl}/api/v1/config/dictionary${params}`
        );
        if (res.ok) {
          const data = await res.json();
          setTerms(data);
        }
      } catch (e) {
        console.error("Failed to fetch terms", e);
      }
    };

    fetchTerms();
  }, [daemonUrl, currentProjectId, status]);

  const t = (key: string, defaultVal?: string) => {
    const lowerKey = key.toLowerCase();
    if (terms[lowerKey]) return terms[lowerKey];
    return defaultVal || key;
  };

  return (
    <TermContext.Provider value={{ terms, t }}>{children}</TermContext.Provider>
  );
}

export const useTerms = () => useContext(TermContext);
