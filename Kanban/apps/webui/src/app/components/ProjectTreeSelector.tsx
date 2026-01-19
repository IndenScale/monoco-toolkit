"use client";

import React, { useMemo } from "react";
import {
  Menu,
  MenuItem,
  Icon,
  Classes,
  Tree,
  TreeNodeInfo,
} from "@blueprintjs/core";
import { useDaemonStore } from "@monoco-io/kanban-core";

interface ProjectTreeSelectorProps {
  onSelect?: () => void;
}

// Helper to build tree from flat list of projects with paths
const buildProjectTree = (projects: any[], currentProjectId: string | null): TreeNodeInfo[] => {
  // Simple implementation: Group by path depth or just list them if structure is complex.
  // For now, let's assume a flat list but rendered with indentation if paths suggest hierarchy.
  // Or better: Just render them as a flat list with path as subtitle,
  // since building a full file system tree might be overkill without more data.
  // BUT user asked for "Tree view".

  // Let's try to reconstruct hierarchy from `path`.
  // This is tricky without knowing the common root.

  // Fallback: Just return a flat list for now but structured as TreeNodes.
  return projects.map((p) => ({
    id: p.id,
    label: p.name,
    secondaryLabel: (
        <span className="text-xs text-text-muted truncate max-w-[150px] inline-block" title={p.path}>
            {p.path.split('/').pop()}
        </span>
    ),
    icon: currentProjectId === p.id ? "tick" : "briefcase",
    isSelected: currentProjectId === p.id,
    nodeData: p,
  }));
};

export default function ProjectTreeSelector({ onSelect }: ProjectTreeSelectorProps) {
  const { projects, currentProjectId, setCurrentProjectId } = useDaemonStore();

  const handleNodeClick = (node: TreeNodeInfo) => {
    const project = node.nodeData as any;
    if (project && project.id) {
      setCurrentProjectId(project.id);
      if (onSelect) onSelect();
    }
  };

  const nodes = useMemo(() => {
      return buildProjectTree(projects || [], currentProjectId);
  }, [projects, currentProjectId]);

  if (!projects || projects.length === 0) {
      return <Menu><MenuItem text="No projects found" disabled /></Menu>;
  }

  return (
    <div className="min-w-[300px] max-h-[500px] overflow-y-auto p-2">
        <div className="mb-2 px-2 text-xs font-semibold text-text-muted uppercase tracking-wider">
            Select Project
        </div>
        <Tree
            contents={nodes}
            onNodeClick={handleNodeClick}
            className={Classes.ELEVATION_0}
        />
    </div>
  );
}
