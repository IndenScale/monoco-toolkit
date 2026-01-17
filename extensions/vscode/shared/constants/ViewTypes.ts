/**
 * View type identifiers
 */

export const VIEW_TYPES = {
  KANBAN: "monoco.kanbanView",
  EXECUTIONS: "monoco.actionsView",
} as const;

export type ViewType = (typeof VIEW_TYPES)[keyof typeof VIEW_TYPES];
