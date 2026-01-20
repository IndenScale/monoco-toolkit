/**
 * Document Link Provider
 * Provides clickable links for issue IDs in documents
 */

import { DocumentLink, DocumentLinkParams, Range } from 'vscode-languageserver/node'
import { TextDocument } from 'vscode-languageserver-textdocument'
import { WorkspaceIndexer } from '../services/WorkspaceIndexer'

export class DocumentLinkProvider {
  constructor(private workspaceIndexer: WorkspaceIndexer) {}

  /**
   * Provide document links
   */
  provideDocumentLinks(
    params: DocumentLinkParams,
    document: TextDocument | undefined
  ): DocumentLink[] {
    if (!document) {
      return []
    }

    const text = document.getText()
    const links: DocumentLink[] = []

    // Regex for Issue IDs: (EPIC|FEAT|CHORE|FIX|ARCH)-\d{4}
    const pattern = /\b((?:EPIC|FEAT|CHORE|FIX|ARCH)-\d{4})\b/g
    let match

    while ((match = pattern.exec(text)) !== null) {
      const id = match[1]
      const issue = this.workspaceIndexer.getIssue(id)

      if (issue) {
        const start = document.positionAt(match.index)
        const end = document.positionAt(match.index + id.length)

        links.push({
          range: Range.create(start, end),
          target: issue.uri,
          tooltip: `${issue.type.toUpperCase()}: ${issue.title} (${issue.status})`,
        })
      }
    }

    return links
  }
}
