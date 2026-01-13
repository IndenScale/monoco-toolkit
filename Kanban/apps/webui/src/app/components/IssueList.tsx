"use client";

import React from "react";
import { useKanbanStore } from "@monoco-io/kanban-core";
import {
  Card,
  Button,
  H5,
  Tag,
  Spinner,
  Intent,
  Elevation,
  Icon,
} from "@blueprintjs/core";

import ProjectEndpointBadge from "./ProjectEndpointBadge";

export default function IssueList() {
  const { issues, isLoading, fetchIssues } = useKanbanStore();

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner intent={Intent.PRIMARY} size={50} />
      </div>
    );
  }

  const getStatusIntent = (status: string): Intent => {
    switch (status) {
      case "closed":
        return Intent.SUCCESS;
      case "open":
        return Intent.PRIMARY;
      case "backlog":
        return Intent.NONE;
      default:
        return Intent.NONE;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <H5 className="mb-0">Issues ({issues.length})</H5>
          <ProjectEndpointBadge />
        </div>
        <Button
          icon="refresh"
          text="Refresh"
          onClick={() => fetchIssues()}
          minimal
        />
      </div>

      <div className="grid gap-4">
        {issues.map((issue) => (
          <Card
            key={issue.id}
            elevation={Elevation.ONE}
            className="flex flex-col gap-2">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-gray-500 text-sm">
                    {issue.id}
                  </span>
                  <Tag minimal intent="none">
                    {issue.type}
                  </Tag>
                  <h4 className="font-medium text-lg m-0">{issue.title}</h4>
                </div>
                <div className="text-gray-500 text-sm flex gap-4">
                  <span>Created: {issue.created_at}</span>
                </div>
              </div>

              <div className="flex gap-2">
                <Tag intent={getStatusIntent(issue.status)}>
                  {issue.status.toUpperCase()}
                </Tag>
              </div>
            </div>

            {/* Relationships */}
            <div className="flex flex-wrap gap-4 text-sm mt-2 pt-2 border-t border-gray-100">
              {issue.parent && (
                <div className="flex items-center gap-1 text-gray-600">
                  <Icon icon="arrow-up" size={12} />
                  <span className="font-semibold">Parent:</span>
                  <span className="font-mono bg-gray-100 px-1 rounded">
                    {issue.parent}
                  </span>
                </div>
              )}
              {issue.dependencies && issue.dependencies.length > 0 && (
                <div className="flex items-center gap-1 text-gray-600">
                  <Icon icon="arrow-right" size={12} />
                  <span className="font-semibold">Deps:</span>
                  <div className="flex gap-1">
                    {issue.dependencies.map((d) => (
                      <span
                        key={d}
                        className="font-mono bg-gray-100 px-1 rounded">
                        {d}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {issue.related && issue.related.length > 0 && (
                <div className="flex items-center gap-1 text-gray-600">
                  <Icon icon="link" size={12} />
                  <span className="font-semibold">Related:</span>
                  <div className="flex gap-1">
                    {issue.related.map((r) => (
                      <span
                        key={r}
                        className="font-mono bg-gray-100 px-1 rounded">
                        {r}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
