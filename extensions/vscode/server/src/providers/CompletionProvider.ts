/**
 * Completion Provider
 * Provides auto-completion for issue IDs
 */

import {
  CompletionItem,
  CompletionItemKind,
  TextDocumentPositionParams,
} from 'vscode-languageserver/node'
import { WorkspaceIndexer } from '../services/WorkspaceIndexer'

export class CompletionProvider {
  constructor(private workspaceIndexer: WorkspaceIndexer) {}

  /**
   * Provide completion items
   */
  provideCompletion(_params: TextDocumentPositionParams): CompletionItem[] {
    return this.workspaceIndexer.getAllIssues().map((issue) => ({
      label: issue.id,
      kind: CompletionItemKind.Reference,
      detail: `${issue.type} - ${issue.stage}`,
      documentation: issue.title,
      data: issue.id,
    }))
  }

  /**
   * Resolve completion item (optional)
   */
  resolveCompletion(item: CompletionItem): CompletionItem {
    return item
  }
}
