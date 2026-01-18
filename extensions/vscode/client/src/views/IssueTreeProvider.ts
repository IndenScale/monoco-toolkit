import * as vscode from "vscode";
import { Issue, IssueTreeItem } from "./IssueTreeItem";
import { FilterState } from "./IssueFilterWebviewProvider";

/**
 * Native TreeView provider for Issues
 * Replaces the webview-based issue list
 */
export class IssueTreeProvider
  implements
    vscode.TreeDataProvider<IssueTreeItem>,
    vscode.TreeDragAndDropController<IssueTreeItem>
{
  private _onDidChangeTreeData = new vscode.EventEmitter<
    IssueTreeItem | undefined | void
  >();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  // Drag and drop MIME type
  readonly dropMimeTypes = ["application/vnd.code.tree.monoco"];
  readonly dragMimeTypes = ["text/uri-list", "text/plain"];

  private issues: Issue[] = [];

  private filterState: FilterState = {
    project: null,
    types: [],
    statuses: [],
    stages: [],
    tagQuery: "",
  };
  private searchQuery: string = "";

  constructor() {}

  /**
   * Update issues data from LSP
   */
  updateIssues(issues: Issue[]): void {
    this.issues = issues;
    this.refresh();
  }

  /**
   * Set active filters
   */
  setFilter(state: FilterState): void {
    this.filterState = state;
    this.refresh();
  }

  /**
   * Set active project filter (Compatibility)
   */
  setProject(projectId: string | null): void {
    this.filterState.project = projectId === "all" ? null : projectId;
    this.refresh();
  }

  /**
   * Set search query filter
   */
  setSearchQuery(query: string): void {
    this.searchQuery = query.toLowerCase();
    this.refresh();
  }

  /**
   * Refresh the tree
   */
  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  /**
   * Get tree item representation
   */
  getTreeItem(element: IssueTreeItem): vscode.TreeItem {
    return element;
  }

  /**
   * Get children for tree hierarchy
   */
  async getChildren(element?: IssueTreeItem): Promise<IssueTreeItem[]> {
    if (!element) {
      // Root level: return filtered root issues
      return this.getRootIssues();
    } else if (element.issue.id === "untracked-root") {
      // Untracked group: return orphan atomic issues
      return this.getUntrackedIssues();
    } else {
      // Child level: return children of the given issue
      return this.getChildIssues(element.issue);
    }
  }

  /**
   * Get parent of an item (for reveal/navigation)
   */
  getParent(element: IssueTreeItem): vscode.ProviderResult<IssueTreeItem> {
    if (element.issue.id === "untracked-root") {
      return null;
    }

    if (!element.issue.parent) {
      // Check if it's an atomic issue acting as a root (would be in Untracked)
      if (this.isAtomic(element.issue)) {
        // This is complex because we don't hold a reference to the virtual parent.
        // For now, return null as reveal might not strictly require it for virtual nodes.
        return null;
      }
      return null;
    }

    const parentIssue = this.issues.find((i) => i.id === element.issue.parent);
    if (!parentIssue) {
      return null;
    }

    const children = this.getChildrenOfIssue(parentIssue);
    return new IssueTreeItem(
      parentIssue,
      children.length,
      children.length > 0
        ? vscode.TreeItemCollapsibleState.Collapsed
        : vscode.TreeItemCollapsibleState.None,
    );
  }

  /**
   * Get root issues (no parent or parent not in current project)
   */
  private async getRootIssues(): Promise<IssueTreeItem[]> {
    // Filter by project
    let filtered = this.applyFilters(this.issues);

    // Build parent-child map
    const idMap = new Map(filtered.map((i) => [i.id, i]));

    // Find roots
    const roots = filtered.filter((issue) => {
      if (!issue.parent) {
        return true;
      }
      return !idMap.has(issue.parent);
    });

    // Filter by search
    const searchFiltered = this.searchQuery
      ? roots.filter((i) => this.matchesSearch(i))
      : roots;

    // Separate into Collections (Epic/Arch) and Orphans (Atomic)
    const collections: Issue[] = [];
    const orphans: Issue[] = [];

    for (const issue of searchFiltered) {
      if (this.isCollection(issue)) {
        collections.push(issue);
      } else {
        orphans.push(issue);
      }
    }

    // Sort Collections
    collections.sort((a, b) => this.compareIssues(a, b));

    const result: IssueTreeItem[] = [];

    // Add Collections
    for (const issue of collections) {
      const children = this.getChildrenOfIssue(issue);
      result.push(
        new IssueTreeItem(
          issue,
          children.length,
          children.length > 0 // Collections without children are still collections, but logic here determines expandability
            ? vscode.TreeItemCollapsibleState.Collapsed
            : vscode.TreeItemCollapsibleState.None,
        ),
      );
    }

    // Handle Orphans -> "Untracked Issues"
    if (orphans.length > 0) {
      const untrackedGroup: Issue = {
        id: "untracked-root",
        title: "Untracked Issues",
        type: "epic", // Dummy type
        status: "open",
        stage: "doing", // Dummy stage
        tags: [],
      };
      // Use a special icon or state for this group?
      // IssueTreeItem might need custom logic for this ID, but for now we pass it as a regular item
      result.push(
        new IssueTreeItem(
          untrackedGroup,
          orphans.length,
          vscode.TreeItemCollapsibleState.Collapsed,
        ),
      );
    }

    return result;
  }

  /**
   * Get untracked atomic issues
   */
  private async getUntrackedIssues(): Promise<IssueTreeItem[]> {
    // Filter by project
    let filtered = this.applyFilters(this.issues);
    const idMap = new Map(filtered.map((i) => [i.id, i]));

    const roots = filtered.filter((issue) => {
      if (!issue.parent) {
        return true;
      }
      return !idMap.has(issue.parent);
    });

    const searchFiltered = this.searchQuery
      ? roots.filter((i) => this.matchesSearch(i))
      : roots;

    const orphans = searchFiltered.filter((i) => !this.isCollection(i));

    // Sort orphans
    orphans.sort((a, b) => this.compareIssues(a, b));

    return orphans.map((issue) => {
      const children = this.getChildrenOfIssue(issue);
      return new IssueTreeItem(
        issue,
        children.length,
        children.length > 0
          ? vscode.TreeItemCollapsibleState.Collapsed
          : vscode.TreeItemCollapsibleState.None,
      );
    });
  }

  /**
   * Get child issues of a parent
   */
  private async getChildIssues(parent: Issue): Promise<IssueTreeItem[]> {
    const children = this.getChildrenOfIssue(parent);

    // Filter by search
    const searchFiltered = this.searchQuery
      ? children.filter((i) => this.matchesSearch(i))
      : children;

    // Sort
    searchFiltered.sort((a, b) => this.compareIssues(a, b));

    return searchFiltered.map((issue) => {
      const grandChildren = this.getChildrenOfIssue(issue);
      return new IssueTreeItem(
        issue,
        grandChildren.length,
        grandChildren.length > 0
          ? vscode.TreeItemCollapsibleState.Collapsed
          : vscode.TreeItemCollapsibleState.None,
      );
    });
  }

  /**
   * Get direct children of an issue
   */
  private getChildrenOfIssue(issue: Issue): Issue[] {
    return this.issues.filter((i) => i.parent === issue.id);
  }

  /**
   * Filter issues by selected project
   */
  /**
   * Filter issues by all criteria
   */
  private applyFilters(issues: Issue[]): Issue[] {
    return issues.filter((i) => {
      // 1. Project
      if (this.filterState.project) {
        if (this.filterState.project === "root") {
          if (i.project_id) return false;
        } else {
          if (i.project_id !== this.filterState.project) return false;
        }
      }

      // 2. Type
      if (this.filterState.types.length > 0) {
        if (!this.filterState.types.includes(i.type)) return false;
      }

      // 3. Status
      if (this.filterState.statuses.length > 0) {
        if (!this.filterState.statuses.includes(i.status)) return false;
      }

      // 4. Stage
      if (this.filterState.stages.length > 0) {
        if (!this.filterState.stages.includes(i.stage)) return false;
      }

      // 5. Tags
      if (this.filterState.tagQuery) {
        if (!this.matchesTags(i, this.filterState.tagQuery)) return false;
      }

      return true;
    });
  }

  /**
   * Parse and match tags
   * Supports: +required, -excluded, optional (nice to have - treated as optional match?)
   * User Request: "+#tag1 -#tag2 #tag3"
   * Implementation:
   *  - Terms starting with +: MUST HAVE
   *  - Terms starting with -: MUST NOT HAVE
   *  - Terms without prefix: OR match (if any 'optional' terms exist, must match at least one? Or just standard search?)
   *    Let's go with: If there are "optional" terms, the item must match at least one of them UNLESS only required/excluded terms are present.
   */
  private matchesTags(issue: Issue, query: string): boolean {
    const tokens = query.split(/\s+/).filter((t) => t.length > 0);
    if (tokens.length === 0) return true;

    const required: string[] = [];
    const excluded: string[] = [];
    const optional: string[] = [];

    tokens.forEach((t) => {
      if (t.startsWith("+"))
        required.push(t.slice(1).replace(/^#/, "")); // Remove + and optional #
      else if (t.startsWith("-"))
        excluded.push(t.slice(1).replace(/^#/, "")); // Remove - and optional #
      else optional.push(t.replace(/^#/, "")); // Remove optional #
    });

    const issueTags = issue.tags || [];

    // 1. Check Excluded (Fail fast)
    for (const ex of excluded) {
      if (issueTags.includes(ex)) return false;
    }

    // 2. Check Required
    for (const req of required) {
      if (!issueTags.includes(req)) return false;
    }

    // 3. Check Optional
    // If optional terms exist, usually in search logic it means "Must match one of these" OR "Just boost score".
    // Since this is a hard filter, "Must match at least one" is the standard interpretation of mixed boolean queries usually,
    // UNLESS it's purely a "Nice to have" (sorting).
    // Warning: If I make it strict, "#tag3" filters out everything else. This seems to be what "filter" means.
    if (optional.length > 0) {
      const hasMatch = optional.some((opt) => issueTags.includes(opt));
      if (!hasMatch) return false;
    }

    return true;
  }

  /**
   * Check if issue matches search query
   */
  private matchesSearch(issue: Issue): boolean {
    if (!this.searchQuery) {
      return true;
    }
    const title = (issue.title || "").toLowerCase();
    const id = (issue.id || "").toLowerCase();
    return title.includes(this.searchQuery) || id.includes(this.searchQuery);
  }

  private isCollection(issue: Issue): boolean {
    return issue.type === "epic" || issue.type === "arch";
  }

  private isAtomic(issue: Issue): boolean {
    return !this.isCollection(issue);
  }

  /**
   * Comprehensive sort function: Type -> Status -> Stage -> Title
   */
  private compareIssues(a: Issue, b: Issue): number {
    // 1. Sort by Type Priority
    const typeWeight = (type: string) => {
      switch (type) {
        case "epic":
          return 0;
        case "arch":
          return 1;
        case "feature":
          return 2;
        case "bug":
          return 3;
        case "fix":
          return 4;
        case "chore":
          return 5;
        default:
          return 99;
      }
    };
    const typeDiff = typeWeight(a.type) - typeWeight(b.type);
    if (typeDiff !== 0) {
      return typeDiff;
    }

    // 2. Sort by Status/Stage Weight
    const statusDiff = this.statusWeight(a) - this.statusWeight(b);
    if (statusDiff !== 0) {
      return statusDiff;
    }

    // 3. Sort by ID (usually implies creation time roughly, or at least consistent)
    return a.id.localeCompare(b.id);
  }

  /**
   * Status weight for sorting
   */
  private statusWeight(issue: Issue): number {
    const map: Record<string, number> = {
      // Active states
      doing: 0,
      review: 1,
      draft: 2,
      // Pending
      backlog: 5,
      // Done - keep them at bottom
      done: 8,
      closed: 9,
    };
    // Prioritize stage, then status
    return map[issue.stage] ?? map[issue.status] ?? 4; // Default to middle
  }

  // ===== Drag and Drop Implementation =====

  /**
   * Handle drag start - export issue path/ID
   */
  async handleDrag(
    source: readonly IssueTreeItem[],
    dataTransfer: vscode.DataTransfer,
    _token: vscode.CancellationToken,
  ): Promise<void> {
    if (source.length === 0) {
      return;
    }

    const item = source[0];
    const issue = item.issue;

    // Set file URI for drag to terminal/editor
    if (issue.path) {
      const uri = vscode.Uri.file(issue.path);
      dataTransfer.set(
        "text/uri-list",
        new vscode.DataTransferItem(uri.toString()),
      );
      dataTransfer.set("text/plain", new vscode.DataTransferItem(issue.path));
    } else {
      // Fallback: just the ID
      dataTransfer.set("text/plain", new vscode.DataTransferItem(issue.id));
    }

    // Custom MIME type for internal handling
    dataTransfer.set(
      "application/vnd.code.tree.monoco",
      new vscode.DataTransferItem(JSON.stringify(issue)),
    );
  }

  /**
   * Handle drop - for reparenting issues (future feature)
   */
  async handleDrop(
    _target: IssueTreeItem | undefined,
    _dataTransfer: vscode.DataTransfer,
    _token: vscode.CancellationToken,
  ): Promise<void> {
    // Future: implement reparenting by dropping one issue onto another
    // For now, we only support drag-out to terminal/editor
  }
}
