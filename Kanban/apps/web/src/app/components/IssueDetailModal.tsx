import React, { useEffect, useState } from "react";
import {
  Dialog,
  Classes,
  Button,
  Intent,
  Spinner,
  Tag,
  Callout,
  Divider,
} from "@blueprintjs/core";
import Editor from "@monaco-editor/react";
import { Issue } from "../types";
import { useDaemonStore } from "@monoco/kanban-core";
import { useTerms } from "../contexts/TermContext";

interface IssueDetailModalProps {
  issueId: string | null;
  onClose: () => void;
}

export default function IssueDetailModal({
  issueId,
  onClose,
}: IssueDetailModalProps) {
  // @ts-ignore
  const { daemonUrl, currentProjectId } = useDaemonStore();
  const [issue, setIssue] = useState<Issue | null>(null);
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { t } = useTerms();

  useEffect(() => {
    // ... (fetch logic remains same) ...
    if (!issueId || !daemonUrl) {
      setIssue(null);
      return;
    }

    const fetchIssue = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = currentProjectId
          ? `?project_id=${currentProjectId}`
          : "";
        const res = await fetch(
          `${daemonUrl}/api/v1/issues/${issueId}${params}`
        );
        if (!res.ok) throw new Error("Failed to load issue");
        const data = await res.json();
        setIssue(data);
        setEditContent(data.raw_content || data.body || "");
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchIssue();
    setIsEditing(false);
  }, [issueId, daemonUrl, currentProjectId]);

  const handleSave = async () => {
      // ... (handleSave logic remains same) ...
    if (!issueId || !daemonUrl) return;

    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${daemonUrl}/api/v1/issues/${issueId}/content`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            content: editContent,
            project_id: currentProjectId,
          }),
        }
      );

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to save issue");
      }

      setIsEditing(false);
      
      const params = currentProjectId ? `?project_id=${currentProjectId}` : "";
      const refreshRes = await fetch(`${daemonUrl}/api/v1/issues/${issueId}${params}`);
      if (refreshRes.ok) {
          const refreshedData = await refreshRes.json();
          setIssue(refreshedData);
          setEditContent(refreshedData.raw_content || refreshedData.body || "");
      }

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTransition = async (newStage: string) => {
    if (!issueId || !daemonUrl) return;
    setLoading(true);
    try {
        const res = await fetch(`${daemonUrl}/api/v1/issues/${issueId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stage: newStage, project_id: currentProjectId })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Failed to transition issue");
        }
        // Refresh
        const params = currentProjectId ? `?project_id=${currentProjectId}` : "";
        const refreshRes = await fetch(`${daemonUrl}/api/v1/issues/${issueId}${params}`);
        if (refreshRes.ok) {
            setIssue(await refreshRes.json());
        }
    } catch (err: any) {
        setError(err.message);
    } finally {
        setLoading(false);
    }
  };

  const getStatusIntent = (status: string) => {
    switch (status?.toLowerCase()) {
      case "open":
        return Intent.NONE;
      case "in_progress":
        return Intent.PRIMARY;
      case "done":
        return Intent.SUCCESS;
      case "closed":
        return Intent.DANGER;
      default:
        return Intent.NONE;
    }
  };

  return (
    <Dialog
      isOpen={!!issueId}
      onClose={onClose}
      title={
        issue ? (
          <div className="flex items-center gap-2">
            <span className="font-mono text-text-muted">{issue.id}</span>
            <span className="font-semibold text-lg">{issue.title}</span>
          </div>
        ) : (
          "Loading..."
        )
      }
      className="bp5-dark w-[90vw] h-[90vh] flex flex-col p-0"
      style={{ width: "1200px", maxWidth: "95vw", height: "85vh" }}>
      <div
        className={
          Classes.DIALOG_BODY +
          " flex-1 overflow-hidden flex flex-col p-0 m-0 bg-canvas"
        }>
        {loading && (
          <div className="flex h-full items-center justify-center">
            <Spinner />
          </div>
        )}

        {error && (
          <div className="p-4">
            <Callout intent={Intent.DANGER}>{error}</Callout>
          </div>
        )}

        {!loading && issue && (
          <div className="flex flex-col h-full overflow-hidden">
            {/* Meta Header - Opaque, Structured */}
            <div className="flex flex-col gap-4 p-5 bg-surface border-b border-border-subtle shrink-0">
              <div className="flex items-center justify-between">
                <div className="flex gap-4 items-center">
                  <div className="flex flex-col gap-1">
                    <div className="text-xs text-text-muted uppercase font-bold tracking-wider">
                      Status
                    </div>
                    <Tag intent={getStatusIntent(issue.status)} minimal large>
                      {t(issue.status?.toLowerCase(), issue.status?.toUpperCase())}
                    </Tag>
                  </div>
                  <Divider className="h-8" />
                  <div className="flex flex-col gap-1">
                    <div className="text-xs text-text-muted uppercase font-bold tracking-wider">
                      Stage
                    </div>
                    <div className="text-text-primary font-medium">
                      {issue.stage ? t(issue.stage.toLowerCase(), issue.stage.toUpperCase()) : "-"}
                    </div>
                  </div>
                  <Divider className="h-8" />
                  <div className="flex flex-col gap-1">
                    <div className="text-xs text-text-muted uppercase font-bold tracking-wider">
                      Type
                    </div>
                    <Tag minimal icon="clean">
                      {t(issue.type?.toLowerCase(), issue.type?.toUpperCase())}
                    </Tag>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xs text-text-muted">Created</div>
                  <div className="text-text-secondary font-mono text-sm">
                    {issue.created_at
                      ? new Date(issue.created_at).toLocaleString()
                      : "-"}
                  </div>
                </div>
              </div>

              {/* Optional: Tags or Assignees row could go here */}
              {issue.tags && issue.tags.length > 0 && (
                <div className="flex gap-2">
                  {issue.tags.map((tag) => (
                    <Tag key={tag} minimal round icon="tag">
                      {tag}
                    </Tag>
                  ))}
                </div>
              )}
            </div>

            {/* Content Area - Monaco */}
            <div className="flex-1 min-h-0 relative bg-[#1e1e1e]">
              {/* ^ bg matching vs-dark default */}
              <Editor
                height="100%"
                defaultLanguage="markdown"
                theme="vs-dark"
                value={isEditing ? editContent : issue.body || ""}
                onChange={(val) => setEditContent(val || "")}
                options={{
                  readOnly: !isEditing,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  fontSize: 14,
                  wordWrap: "on",
                  padding: { top: 20, bottom: 20 },
                  lineNumbers: "off", // Cleaner for reading
                  renderLineHighlight: "none",
                  fontFamily: "'JetBrains Mono', monospace",
                }}
              />
            </div>
          </div>
        )}
      </div>
      <div
        className={
          Classes.DIALOG_FOOTER + " bg-surface border-t border-border-subtle"
        }>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          {!isEditing && issue?.stage?.toLowerCase() === 'review' && (
             <>
                <Button 
                    text="Reject" 
                    intent={Intent.DANGER} 
                    icon="cross"
                    onClick={() => handleTransition('doing')} 
                />
                <Button 
                    text="Approve" 
                    intent={Intent.SUCCESS} 
                    icon="tick"
                    onClick={() => handleTransition('done')} 
                />
                <Divider />
             </>
          )}

          {isEditing ? (
            <>
              <Button text="Cancel" onClick={() => setIsEditing(false)} />
              <Button
                text="Save Changes"
                intent={Intent.PRIMARY}
                onClick={handleSave}
              />
            </>
          ) : (
            <>
              <Button text="Close" onClick={onClose} />
              <Button
                text="Edit Issue"
                icon="edit"
                onClick={() => setIsEditing(true)}
              />
            </>
          )}
        </div>
      </div>
    </Dialog>
  );
}
