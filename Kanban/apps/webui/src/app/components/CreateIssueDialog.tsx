import React, { useState, useEffect } from "react";
import {
  Dialog,
  Classes,
  Button,
  FormGroup,
  InputGroup,
  HTMLSelect,
  Intent,
  Spinner,
} from "@blueprintjs/core";
import { useDaemonStore } from "@monoco-io/kanban-core";
import { Issue } from "../types";

interface CreateIssueDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function CreateIssueDialog({
  isOpen,
  onClose,
  onSuccess,
}: CreateIssueDialogProps) {
  // @ts-ignore
  const { daemonUrl, currentProjectId } = useDaemonStore();
  const [title, setTitle] = useState("");
  const [type, setType] = useState("feature");
  const [parentId, setParentId] = useState("");
  const [loading, setLoading] = useState(false);
  const [epics, setEpics] = useState<Issue[]>([]);
  const [loadingEpics, setLoadingEpics] = useState(false);

  useEffect(() => {
    if (isOpen && daemonUrl) {
      fetchEpics();
    }
  }, [isOpen, daemonUrl, currentProjectId]);

  const fetchEpics = async () => {
    setLoadingEpics(true);
    try {
      const params = currentProjectId ? `?project_id=${currentProjectId}` : "";
      const res = await fetch(`${daemonUrl}/api/v1/issues${params}`);
      if (res.ok) {
        const issues: Issue[] = await res.json();
        setEpics(issues.filter((i) => i.type === "epic" && i.status !== "closed"));
      }
    } catch (error) {
      console.error("Failed to fetch epics", error);
    } finally {
      setLoadingEpics(false);
    }
  };

  const handleSubmit = async () => {
    if (!title.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${daemonUrl}/api/v1/issues`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_id: currentProjectId,
          title,
          type,
          parent: parentId || undefined,
          status: "open",
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to create issue");
      }

      setTitle("");
      setType("feature");
      setParentId("");
      onSuccess();
      onClose();
    } catch (error) {
      console.error(error);
      // You might want to show a toaster here
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Create New Issue"
      className="pb-0"
    >
      <div className={Classes.DIALOG_BODY}>
        <FormGroup label="Title" labelFor="title-input" intent={Intent.PRIMARY}>
          <InputGroup
            id="title-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Implement Login Page"
          />
        </FormGroup>

        <div className="flex gap-4">
          <FormGroup label="Type" labelFor="type-select" className="flex-1">
            <HTMLSelect
              id="type-select"
              value={type}
              onChange={(e) => setType(e.target.value)}
              fill
            >
              <option value="feature">Feature</option>
              <option value="chore">Chore</option>
              <option value="fix">Fix</option>
              <option value="epic">Epic</option>
            </HTMLSelect>
          </FormGroup>

          <FormGroup label="Parent Epic" labelFor="epic-select" className="flex-1">
            <HTMLSelect
              id="epic-select"
              value={parentId}
              onChange={(e) => setParentId(e.target.value)}
              fill
              disabled={type === "epic" || loadingEpics}
            >
              <option value="">None</option>
              {epics.map((epic) => (
                <option key={epic.id} value={epic.id}>
                  {epic.id}: {epic.title}
                </option>
              ))}
            </HTMLSelect>
          </FormGroup>
        </div>
      </div>
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            intent={Intent.PRIMARY}
            onClick={handleSubmit}
            loading={loading}
            disabled={!title.trim()}
          >
            Create
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
