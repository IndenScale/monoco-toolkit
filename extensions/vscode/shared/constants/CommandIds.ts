/**
 * Command identifiers
 */

export const COMMAND_IDS = {
  // Kanban commands
  OPEN_KANBAN: 'monoco.openKanban',
  REFRESH_ENTRY: 'monoco.refreshEntry',
  CREATE_ISSUE: 'monoco.createIssue',
  OPEN_SETTINGS: 'monoco.openSettings',
  OPEN_WEB_UI: 'monoco.openWebUI',

  // Issue commands
  TOGGLE_STATUS: 'monoco.toggleStatus',
  TOGGLE_STAGE: 'monoco.toggleStage',

  // Action commands
  RUN_ACTION: 'monoco.runAction',
  SHOW_AGENT_ACTIONS: 'monoco.showAgentActions',
  VIEW_ACTION_TEMPLATE: 'monoco.viewActionTemplate',
  REFRESH_PROVIDERS: 'monoco.refreshProviders',

  // Utility commands
  RUN_TERMINAL_COMMAND: 'monoco.runTerminalCommand',
  CHECK_DEPENDENCIES: 'monoco.checkDependencies',
} as const

export type CommandId = (typeof COMMAND_IDS)[keyof typeof COMMAND_IDS]
