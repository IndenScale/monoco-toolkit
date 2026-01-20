/**
 * Core Issue types shared between client, server, and webview
 */

export type IssueType = 'epic' | 'feature' | 'chore' | 'fix'

export type IssueStatus = 'open' | 'closed' | 'backlog'

export type IssueStage = 'draft' | 'ready' | 'in_progress' | 'review' | 'done' | 'archived'

/**
 * Issue metadata from frontmatter
 */
export interface IssueMetadata {
  id: string
  uid?: string
  type: IssueType
  title: string
  status: IssueStatus
  stage: IssueStage
  parent?: string
  solution?: string
  dependencies?: string[]
  related?: string[]
  tags?: string[]
  created_at?: string
  updated_at?: string
  opened_at?: string
  closed_at?: string
}

/**
 * Issue index entry used by LSP server
 */
export interface IssueIndex extends IssueMetadata {
  project_id: string
  filePath: string
  uri: string
}

/**
 * Issue creation request
 */
export interface CreateIssueRequest {
  type: IssueType
  title: string
  parent?: string
  dependencies?: string[]
  related?: string[]
  tags?: string[]
}

/**
 * Issue update request
 */
export interface UpdateIssueRequest {
  id: string
  changes: Partial<IssueMetadata>
}
