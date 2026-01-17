import { StateManager, AppState } from "../state/StateManager";
import { VSCodeBridge } from "../services/VSCodeBridge";
import { IssueIndex } from "@shared/types/Issue";
import { getIcon, escapeHtml, ICONS } from "../utils/helpers";

/**
 * Issue tree component
 * Renders hierarchical issue tree with search and filtering
 */
export class IssueTree {
  private container: HTMLElement;

  constructor(
    container: HTMLElement,
    private stateManager: StateManager,
    private bridge: VSCodeBridge,
  ) {
    this.container = container;

    // Subscribe to state changes
    this.stateManager.subscribe((state) => this.render(state));
  }

  /**
   * Render the issue tree
   */
  render(state: Readonly<AppState>) {
    this.container.innerHTML = "";
    const { issues, searchQuery } = state;

    // 1. Filter by project & advanced filters
    let targetIssues = this.filterIssues(issues, state);

    if (targetIssues.length === 0) {
      this.container.innerHTML = `<div class="empty-state">No issues to display. (Total synced: ${issues.length})</div>`;
      return;
    }

    // 2. Build tree structure
    const { idMap, childrenMap } = this.buildMaps(targetIssues);

    // 3. Separate issues into collections and untracked
    const collections: IssueIndex[] = [];
    const untracked: IssueIndex[] = [];

    targetIssues.forEach((issue) => {
      const pid = issue.parent || (issue as any).Parent;
      const hasParent = pid && idMap.has(pid);
      const type = (issue.type || "").toLowerCase();
      const isCollection = type === "epic" || type === "arch";

      // Issue is a root if it has no parent or parent is not in filtered set
      if (!hasParent) {
        if (isCollection) {
          collections.push(issue);
        } else {
          untracked.push(issue);
        }
      }
    });

    // 4. Sort collections and untracked by type-id
    const sortByTypeAndId = (a: IssueIndex, b: IssueIndex) => {
      // Extract type prefix and number
      const extractParts = (id: string) => {
        const match = id.match(/^([A-Z]+)-(\d+)$/);
        if (match) {
          return { type: match[1], num: parseInt(match[2], 10) };
        }
        return { type: id, num: 0 };
      };

      const aParts = extractParts(a.id);
      const bParts = extractParts(b.id);

      // First sort by type
      if (aParts.type !== bParts.type) {
        return aParts.type.localeCompare(bParts.type);
      }

      // Then by number
      return aParts.num - bParts.num;
    };

    collections.sort(sortByTypeAndId);
    untracked.sort(sortByTypeAndId);

    // 5. Render tree
    const container = document.createDocumentFragment();

    // Render collections (Epic/Arch)
    collections.forEach((collection) => {
      const children = childrenMap.get(collection.id) || [];
      // Sort children by type-id
      children.sort(sortByTypeAndId);

      // Always render as tree node for epic/arch
      const node = this.createTreeNode(
        collection,
        children,
        0,
        childrenMap,
        searchQuery,
        state.expandedIds,
      );
      if (node) {
        container.appendChild(node);
      }
    });

    // Render untracked issues in a special collection
    if (untracked.length > 0) {
      const untrackedGroup = this.createUntrackedGroup(
        untracked,
        childrenMap,
        searchQuery,
        state.expandedIds,
      );
      container.appendChild(untrackedGroup);
    }

    this.container.appendChild(container);
  }

  private buildMaps(issues: IssueIndex[]) {
    const idMap = new Map(issues.map((i) => [i.id, i]));
    const childrenMap = new Map<string, IssueIndex[]>();

    issues.forEach((i) => {
      const parentId = i.parent || (i as any).Parent;
      if (parentId) {
        if (!childrenMap.has(parentId)) {
          childrenMap.set(parentId, []);
        }
        childrenMap.get(parentId)!.push(i);
      }
    });

    return { idMap, childrenMap };
  }

  /**
   * Filter issues
   */
  /**
   * Filter issues
   */
  private filterIssues(
    issues: IssueIndex[],
    state: Readonly<AppState>,
  ): IssueIndex[] {
    const { selectedProjectId, filters } = state;
    const { status: fStatus, stage: fStage, tags: fTags } = filters;

    return issues
      .filter((issue) => {
        // 1. Project
        if (selectedProjectId && selectedProjectId !== "all") {
          const p = (
            issue.project_id ||
            (issue as any).project ||
            (issue as any).projectId ||
            (issue as any).Project ||
            ""
          )
            .toString()
            .toLowerCase();
          if (p !== selectedProjectId.toLowerCase()) return false;
        }

        // 2. Status (Open, Backlog, Closed)
        const currentStatus = (issue.status || "open").toLowerCase();
        if (fStatus && fStatus.length > 0) {
          if (!fStatus.includes(currentStatus)) return false;
        }

        // 3. Stage (Draft, Ready, Doing, Review, Done)
        const currentStage = (issue.stage || "draft").toLowerCase();
        if (fStage && fStage.length > 0) {
          // Handling alias "doing" vs "in_progress" if necessary, but assuming UI sends matching values
          // or we normalize here.
          let checkStage = currentStage;
          if (checkStage === "in_progress") checkStage = "doing";

          // Also user might select 'doing' but legacy data implies in_progress.
          // Let's assume strict match for now, or normalize.
          // Let's normalize issue stage to matches UI expectations:
          if (currentStage === "in_progress") {
            if (!fStage.includes("doing") && !fStage.includes("in_progress"))
              return false;
          } else {
            if (!fStage.includes(currentStage)) return false;
          }
        }

        // 4. Tags
        const t = issue.tags || [];
        const tags = Array.isArray(t) ? t : [t];

        if (fTags) {
          // Exclude
          if (fTags.exclude && fTags.exclude.length > 0) {
            const hasExcluded = tags.some((tag) => fTags.exclude.includes(tag));
            if (hasExcluded) return false;
          }
          // Include (OR logic)
          if (fTags.include && fTags.include.length > 0) {
            const hasIncluded = tags.some((tag) => fTags.include.includes(tag));
            if (!hasIncluded) return false;
          }
        }

        return true;
      })
      .sort((a, b) => {
        // Nice to have sort boost
        if (fTags && fTags.nice && fTags.nice.length > 0) {
          const aTags = Array.isArray(a.tags) ? a.tags : [];
          const bTags = Array.isArray(b.tags) ? b.tags : [];
          const aBoost = aTags.some((t) => fTags.nice.includes(t)) ? 1 : 0;
          const bBoost = bTags.some((t) => fTags.nice.includes(t)) ? 1 : 0;
          return bBoost - aBoost;
        }
        return 0;
      });
  }

  /**
   * Check if issue matches search query
   */
  private matchesSearch(issue: IssueIndex, query: string): boolean {
    if (!query) {
      return true;
    }
    const t = (issue.title || "").toLowerCase();
    const id = (issue.id || "").toLowerCase();
    return t.includes(query) || id.includes(query);
  }

  /**
   * Render a tree node (recursive)
   */
  private renderNode(
    issue: IssueIndex,
    depth: number,
    childrenMap: Map<string, IssueIndex[]>,
    searchQuery: string,
    expandedIds: Set<string>,
  ): HTMLElement | null {
    if (searchQuery && !this.matchesSearch(issue, searchQuery)) {
      return null;
    }

    const type = (issue.type || "").toLowerCase();
    const isCollection = type === "epic" || type === "arch";
    const children = childrenMap.get(issue.id) || [];

    // Sort children by type-id
    const sortByTypeAndId = (a: IssueIndex, b: IssueIndex) => {
      const extractParts = (id: string) => {
        const match = id.match(/^([A-Z]+)-(\d+)$/);
        if (match) {
          return { type: match[1], num: parseInt(match[2], 10) };
        }
        return { type: id, num: 0 };
      };

      const aParts = extractParts(a.id);
      const bParts = extractParts(b.id);

      if (aParts.type !== bParts.type) {
        return aParts.type.localeCompare(bParts.type);
      }

      return aParts.num - bParts.num;
    };

    children.sort(sortByTypeAndId);

    // Epic/Arch always render as tree node, even without children
    if (isCollection || children.length > 0) {
      return this.createTreeNode(
        issue,
        children,
        depth,
        childrenMap,
        searchQuery,
        expandedIds,
      );
    } else {
      return this.createIssueItem(issue, depth);
    }
  }

  /**
   * Create a tree group node (parent with children)
   */
  private createTreeNode(
    issue: IssueIndex,
    children: IssueIndex[],
    depth: number,
    childrenMap: Map<string, IssueIndex[]>,
    searchQuery: string,
    expandedIds: Set<string>,
  ): HTMLElement {
    const container = document.createElement("div");
    container.className = "tree-group";
    if (depth > 0) {
      container.style.paddingLeft = `${depth * 12}px`;
    }

    const isExpanded = expandedIds.has(issue.id) || !!searchQuery;
    if (!isExpanded) {
      container.classList.add("collapsed");
    }

    // Create header
    const header = this.createTreeHeader(issue, children);

    // Setup interaction
    header.addEventListener("click", () => {
      const wasCollapsed = container.classList.contains("collapsed");
      if (wasCollapsed) {
        container.classList.remove("collapsed");
        this.stateManager.toggleExpanded(issue.id);
      } else {
        container.classList.add("collapsed");
        this.stateManager.toggleExpanded(issue.id);
      }
      this.stateManager.saveToStorage();
    });

    header.setAttribute("draggable", "true");
    header.addEventListener("dragstart", (e) => {
      this.setupDragData(e, issue);
    });

    header.addEventListener("dblclick", (e) => {
      e.stopPropagation();
      this.openFile(issue);
    });

    // Create children list
    const list = document.createElement("div");
    list.className = "tree-group-list";

    children.forEach((child) => {
      const childNode = this.renderNode(
        child,
        depth + 1,
        childrenMap,
        searchQuery,
        expandedIds,
      );
      if (childNode) {
        list.appendChild(childNode);
      }
    });

    container.appendChild(header);
    container.appendChild(list);
    return container;
  }

  /**
   * Create tree group header
   */
  private createTreeHeader(
    issue: IssueIndex,
    children: IssueIndex[],
  ): HTMLElement {
    const header = document.createElement("div");
    header.className = "tree-group-header";

    // Calculate stats
    const stats = { done: 0, review: 0, doing: 0, draft: 0 };
    // Determine primary status for the group itself
    let primaryStatus = "draft";
    const s = (issue.stage || issue.status || "draft").toLowerCase();

    if (s.includes("doing") || s.includes("progress")) primaryStatus = "doing";
    else if (s.includes("review")) primaryStatus = "review";
    else if (s.includes("done")) primaryStatus = "done";
    else if (s.includes("closed")) primaryStatus = "closed";
    else primaryStatus = "draft";

    children.forEach((c) => {
      const cs = (c.stage || c.status || "draft").toLowerCase();
      if (
        cs.includes("done") ||
        cs.includes("closed") ||
        cs.includes("implemented")
      ) {
        stats.done++;
      }
    });

    const total = children.length;
    const openCount = total - stats.done; // Count only non-done issues

    // Status color mapping
    const getStatusColor = (status: string) => {
      if (status === "done" || status === "closed") return "var(--status-done)";
      if (status === "review") return "var(--status-review)";
      if (status === "doing") return "var(--status-doing)";
      return "var(--status-todo)"; // draft
    };
    const statusColor = getStatusColor(primaryStatus);

    const type = (issue.type || "feature").toLowerCase();

    // Unified Header HTML
    header.innerHTML = `
      <div class="card-content">
        <div class="card-left">
           <div class="chevron">${ICONS.CHEVRON}</div>
           <div class="icon type-${type}" style="margin-right: 6px;">${getIcon(issue.type)}</div>
           <div class="title" title="${escapeHtml(issue.title)}">
             ${
               this.stateManager.getState().settings?.ui?.displayId
                 ? `<span class="node-label" style="color:var(--text-secondary); margin-right:6px; font-family: 'Courier New', monospace; font-size: 11px;">[${escapeHtml(issue.id)}]</span>`
                 : ""
             }
             ${escapeHtml(issue.title)}
           </div>
        </div>
        <div class="card-right">
           ${openCount > 0 ? `<div class="tree-group-count">${openCount > 99 ? "99+" : openCount}</div>` : ""}
           <div class="status-dot ${primaryStatus}" style="background-color: ${statusColor};" title="Status: ${s}"></div>
           <div class="item-add-btn" title="Add Sub-issue">${ICONS.PLUS}</div>
        </div>
      </div>
    `;

    // Wire up add button
    const addBtn = header.querySelector(".item-add-btn");
    if (addBtn) {
      addBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        this.bridge.send({
          type: "SHOW_CREATE_VIEW" as any,
          value: { type: "feature", parent: issue.id },
        });
      });
    }

    return header;
  }

  /**
   * Create an issue item (leaf node)
   */
  private createIssueItem(issue: IssueIndex, depth: number): HTMLElement {
    const item = document.createElement("div");
    const isDone =
      (issue.stage as string) === "done" ||
      (issue.status as string) === "closed" ||
      (issue.status as string) === "done";

    item.className = `issue-item ${isDone ? "done" : ""}`;
    item.dataset.id = issue.id;
    if (depth > 0) {
      item.style.paddingLeft = `${depth * 12 + 28}px`;
    }

    // Draggable
    item.setAttribute("draggable", "true");
    item.addEventListener("dragstart", (e) => {
      this.setupDragData(e, issue);
    });

    const type = (issue.type || "feature").toLowerCase();

    // Status logic
    let primaryStatus = "draft";
    const s = (issue.stage || issue.status || "draft").toLowerCase();

    if (s.includes("doing") || s.includes("progress")) primaryStatus = "doing";
    else if (s.includes("review")) primaryStatus = "review";
    else if (s.includes("done")) primaryStatus = "done";
    else if (s.includes("closed")) primaryStatus = "closed";
    else primaryStatus = "draft";

    const getStatusColor = (status: string) => {
      if (status === "done" || status === "closed") return "var(--status-done)";
      if (status === "review") return "var(--status-review)";
      if (status === "doing") return "var(--status-doing)";
      return "var(--status-todo)"; // draft
    };
    const statusColor = getStatusColor(primaryStatus);

    item.innerHTML = `
      <div class="card-content">
        <div class="card-left">
          <div class="icon type-${type}">${getIcon(issue.type)}</div>
          <div class="title" title="${escapeHtml(issue.title)}">
            ${
              this.stateManager.getState().settings?.ui?.displayId
                ? `<span class="node-label" style="color:var(--text-secondary); margin-right:6px; font-family: 'Courier New', monospace; font-size: 11px;">[${escapeHtml(issue.id)}]</span>`
                : ""
            }
            ${escapeHtml(issue.title)}
          </div>
        </div>
        <div class="card-right">
             <div class="status-dot ${primaryStatus}" style="background-color: ${statusColor};" title="Stage: ${escapeHtml(issue.stage || issue.status || "draft")}"></div>
             <div class="item-add-btn" title="Add Sub-issue">${ICONS.PLUS}</div>
        </div>
      </div>
    `;

    // Wire up Add Button
    const addBtn = item.querySelector(".item-add-btn");
    if (addBtn) {
      addBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        this.bridge.send({
          type: "SHOW_CREATE_VIEW" as any,
          value: { type: "feature", parent: issue.id },
        });
      });
    }

    // Click to open file
    item.addEventListener("click", () => {
      this.openFile(issue);
    });

    return item;
  }

  /**
   * Create untracked issues group
   */
  private createUntrackedGroup(
    issues: IssueIndex[],
    childrenMap: Map<string, IssueIndex[]>,
    searchQuery: string,
    expandedIds: Set<string>,
  ): HTMLElement {
    const container = document.createElement("div");
    container.className = "tree-group";

    const virtualId = "UNTRACKED";
    const isExpanded = expandedIds.has(virtualId) || !!searchQuery;
    if (!isExpanded) {
      container.classList.add("collapsed");
    }

    // Create header
    const header = document.createElement("div");
    header.className = "tree-group-header";

    header.innerHTML = `
      <div class="card-content">
        <div class="card-left">
           <div class="chevron">${ICONS.CHEVRON}</div>
           <div class="icon" style="margin-right: 6px;">📋</div>
           <div class="title">Untracked Issues</div>
        </div>
        <div class="card-right">
           <div class="tree-group-count">${issues.length > 99 ? "99+" : issues.length}</div>
        </div>
      </div>
    `;

    // Setup interaction
    header.addEventListener("click", () => {
      const wasCollapsed = container.classList.contains("collapsed");
      if (wasCollapsed) {
        container.classList.remove("collapsed");
        this.stateManager.toggleExpanded(virtualId);
      } else {
        container.classList.add("collapsed");
        this.stateManager.toggleExpanded(virtualId);
      }
      this.stateManager.saveToStorage();
    });

    // Create children list
    const list = document.createElement("div");
    list.className = "tree-group-list";

    issues.forEach((issue) => {
      const node = this.renderNode(
        issue,
        1,
        childrenMap,
        searchQuery,
        expandedIds,
      );
      if (node) {
        list.appendChild(node);
      }
    });

    container.appendChild(header);
    container.appendChild(list);
    return container;
  }

  /**
   * Setup drag data
   */
  private setupDragData(e: DragEvent, issue: IssueIndex) {
    const root = (window as any).monocoConfig?.rootPath;
    let fullPath = (issue as any).path;

    if (!fullPath) {
      e.dataTransfer!.setData("text/plain", issue.id);
      return;
    }

    // Resolve absolute path
    const isAbsolute = fullPath.startsWith("/") || fullPath.match(/^[a-zA-Z]:/);
    if (root && !isAbsolute) {
      const sep = root.includes("\\") ? "\\" : "/";
      const normalizedPath = fullPath.replace(/\\/g, "/");
      const joinedPath =
        root + (root.endsWith(sep) ? "" : sep) + normalizedPath;

      fullPath = joinedPath
        .split("/")
        .reduce((acc: string[], part: string) => {
          if (part === "..") {
            acc.pop();
          } else if (part && part !== ".") {
            acc.push(part);
          }
          return acc;
        }, [])
        .join("/");

      if (!fullPath.startsWith("/") && !fullPath.match(/^[a-zA-Z]:/)) {
        fullPath = "/" + fullPath;
      }
    }

    // Construct file URI
    const pathSegments = fullPath
      .split("/")
      .map((s: string) => encodeURIComponent(s));
    let encodedPath = pathSegments.join("/");
    let fileUri;
    if (fullPath.match(/^[a-zA-Z]:/)) {
      fileUri = "file:///" + encodedPath;
    } else {
      fileUri = "file://" + encodedPath;
    }

    e.dataTransfer!.setData("text/uri-list", fileUri);
    e.dataTransfer!.setData("text/plain", fullPath);
    e.dataTransfer!.setData("application/vnd.code.tree.monoco", fileUri);
    e.dataTransfer!.setData("application/monoco-issue", JSON.stringify(issue));
  }

  /**
   * Open issue file
   */
  private openFile(issue: IssueIndex) {
    if (!(issue as any).path) {
      console.warn("No path for issue", issue);
    }
    this.bridge.openIssueFile((issue as any).path);
  }
}
