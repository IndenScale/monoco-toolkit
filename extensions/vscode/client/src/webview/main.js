// Main logic for the sidebar webview
const vscode = acquireVsCodeApi();

// Configuration & State
let state = {
  issues: [],
  projects: [],
  selectedProjectId: null,
  expandedIds: new Set(),
  workspaceState: {},
  searchQuery: "",
  settings: {
    apiBase: "http://127.0.0.1:8642/api/v1",
    webUrl: "http://127.0.0.1:8642",
  },
};

const ICONS = {
  EPIC: `<svg class="icon"><use href="#icon-epic"/></svg>`,
  FEATURE: `<svg class="icon"><use href="#icon-feature"/></svg>`,
  BUG: `<svg class="icon"><use href="#icon-bug"/></svg>`,
  CHORE: `<svg class="icon"><use href="#icon-chore"/></svg>`,
  CHEVRON: `<svg class="icon"><use href="#icon-chevron"/></svg>`,
  WEB: `<svg class="icon"><use href="#icon-web"/></svg>`,
  SETTINGS: `<svg class="icon"><use href="#icon-settings"/></svg>`,
  PLUS: `<svg class="icon"><use href="#icon-plus"/></svg>`,
  BACK: `<svg class="icon"><use href="#icon-back"/></svg>`,
  EXECUTION: `<svg class="icon"><use href="#icon-execution"/></svg>`,
  ARCH: `<svg class="icon"><use href="#icon-arch"/></svg>`,
};

/**
 * Get SVG icon for a given issue type.
 * @param {string} type
 * @returns {string} The SVG string.
 */
function getIcon(type) {
  const t = (type || "").toUpperCase();
  if (t === "EPIC") return ICONS.EPIC;
  if (t === "ARCH") return ICONS.ARCH;
  if (t === "FEATURE") return ICONS.FEATURE;
  if (t === "BUG") return ICONS.BUG;
  if (t === "CHORE") return ICONS.CHORE;
  if (t === "FIX") return ICONS.BUG;
  return ICONS.FEATURE;
}

// Elements
const els = {
  projectSelector: document.getElementById("project-selector"),
  issueTree: document.getElementById("issue-tree"),
  searchInput: document.getElementById("search-input"),
  // Toolbar removals
  // Views
  viewHome: document.getElementById("view-home"),
  viewCreate: document.getElementById("view-create"),
  viewSettings: document.getElementById("view-settings"),
  // Back Buttons
  btnBackCreate: document.getElementById("btn-back-create"),
  btnBackSettings: document.getElementById("btn-back-settings"),
  // Create Form
  createTitle: document.getElementById("create-title"),
  createType: document.getElementById("create-type"),
  createParent: document.getElementById("create-parent"),
  createProject: document.getElementById("create-project"),
  btnSubmitCreate: document.getElementById("btn-submit-create"),
  // Settings Form
  settingApiBase: document.getElementById("setting-api-base"),
  settingWebUrl: document.getElementById("setting-web-url"),
  btnSaveSettings: document.getElementById("btn-save-settings"),
  // Tabs
  executionList: document.getElementById("execution-list"),
  // Other removals
};

// Initialization
document.addEventListener("DOMContentLoaded", async () => {
  // Init Toolbar Icons
  if (els.btnWeb) els.btnWeb.innerHTML = ICONS.WEB;
  if (els.btnSettings) els.btnSettings.innerHTML = ICONS.SETTINGS;
  if (els.btnAddEpic) els.btnAddEpic.innerHTML = ICONS.PLUS;
  if (els.btnBackCreate) els.btnBackCreate.innerHTML = ICONS.BACK;
  if (els.btnBackSettings) els.btnBackSettings.innerHTML = ICONS.BACK;

  // Restore State
  const previousState = vscode.getState();
  if (previousState) {
    state.expandedIds = new Set(previousState.expandedIds || []);
    state.searchQuery = previousState.searchQuery || "";
    if (els.searchInput) {
      els.searchInput.value = state.searchQuery;
    }
    if (previousState.settings) {
      state.settings = { ...state.settings, ...previousState.settings };
    }
  }

  // Config Injection (Overrides saved settings if provided by extension)
  if (window.monocoConfig) {
    state.settings.apiBase =
      window.monocoConfig.apiBase || state.settings.apiBase;
    state.settings.webUrl = window.monocoConfig.webUrl || state.settings.webUrl;
  }

  // Event Listeners
  window.addEventListener("message", async (event) => {
    const message = event.data;
    console.log("[Webview] Received message:", message.type, message);

    if (message.type === "REFRESH") refreshAll();
    if (message.type === "DATA_UPDATED") {
      handleDataUpdate(message.payload);
    }
    if (message.type === "EXECUTION_PROFILES") {
      renderExecutionProfiles(message.value);
    }
  });

  function handleDataUpdate(payload) {
    console.log("[Webview] DATA_UPDATED payload received:", payload);
    console.log("[Webview] Payload issues count:", payload?.issues?.length);
    console.log("[Webview] Payload projects count:", payload?.projects?.length);

    state.issues = payload.issues || [];
    state.projects = payload.projects || [];

    if (state.issues.length > 0) {
      console.log("[Webview] First issue sample:", state.issues[0]);
    } else {
      console.warn("[Webview] No issues in payload!");
    }

    if (payload.workspaceState) {
      state.workspaceState = payload.workspaceState;
    }

    if (!state.selectedProjectId || state.selectedProjectId === "all") {
      state.selectedProjectId =
        state.workspaceState.last_active_project_id || "all";
    }

    console.log("[Webview] Targeting project:", state.selectedProjectId);
    console.log(
      "[Webview] About to render with",
      state.issues.length,
      "issues",
    );
    renderProjectSelector();
    renderTree();
    console.log("[Webview] Render complete");
  }

  // Tab switching removal

  // ... (Rest of event listeners logic)

  els.projectSelector.addEventListener("change", async (e) => {
    await setActiveProject(e.target.value);
  });

  els.searchInput?.addEventListener("input", (e) => {
    state.searchQuery = e.target.value.toLowerCase();
    saveLocalState();
    renderTree();
  });

  // Navigation removals

  els.btnBackCreate?.addEventListener("click", () => showView("view-home"));
  els.btnBackSettings?.addEventListener("click", () => showView("view-home"));

  // Form Submission
  els.btnSubmitCreate?.addEventListener("click", async () => {
    await performCreateIssueFromForm();
  });

  // Drag & Drop for Create Parent
  if (els.createParent) {
    els.createParent.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "copy";
      els.createParent.style.borderColor = "var(--vscode-focusBorder)";
    });
    els.createParent.addEventListener("dragleave", () => {
      els.createParent.style.borderColor = "";
    });
    els.createParent.addEventListener("drop", (e) => {
      e.preventDefault();
      els.createParent.style.borderColor = "";
      const raw = e.dataTransfer.getData("application/monoco-issue");
      if (raw) {
        try {
          const droppedIssue = JSON.parse(raw);
          if (droppedIssue && droppedIssue.id) {
            // Add option if missing
            let optionExists = false;
            for (let opt of els.createParent.options) {
              if (opt.value === droppedIssue.id) {
                optionExists = true;
                break;
              }
            }
            if (!optionExists) {
              const opt = document.createElement("option");
              opt.value = droppedIssue.id;
              opt.textContent = `${droppedIssue.id}: ${droppedIssue.title}`;
              els.createParent.appendChild(opt);
            }
            els.createParent.value = droppedIssue.id;
          }
        } catch (e) {
          console.error("Drop failed", e);
        }
      }
    });
  }

  els.btnSaveSettings?.addEventListener("click", () => {
    state.settings.apiBase = els.settingApiBase.value.trim();
    state.settings.webUrl = els.settingWebUrl.value.trim();
    saveLocalState();
    refreshAll(); // Reload with new API

    // Collapse settings view
    els.viewSettings.classList.remove("expanded");
    document.getElementById("primary-views").classList.remove("collapsed");
  });

  // Settings Bottom Sheet Toggle
  const settingsToggle = document.getElementById("settings-toggle-btn");
  if (settingsToggle) {
    settingsToggle.addEventListener("click", () => {
      const isExpanded = els.viewSettings.classList.toggle("expanded");
      const primary = document.getElementById("primary-views");

      if (isExpanded) {
        primary.classList.add("collapsed");
      } else {
        primary.classList.remove("collapsed");
      }
    });
  }

  // Initial Load
  await refreshAll();
  setInterval(refreshAll, 10000);
});

function showView(viewId) {
  document
    .querySelectorAll(".view")
    .forEach((el) => el.classList.remove("active"));
  document.getElementById(viewId).classList.add("active");
}

async function refreshAll() {
  console.log("[Webview] Sending GET_LOCAL_DATA request to extension");
  vscode.postMessage({ type: "GET_LOCAL_DATA" });
}

async function setActiveProject(projectId) {
  state.selectedProjectId = projectId;
  vscode.postMessage({
    type: "SAVE_STATE",
    key: "last_active_project_id",
    value: projectId,
  });
  renderTree();
}

async function fetchIssues(projectId) {
  // Now handled by extension pushing DATA_UPDATED
  refreshAll();
}

function renderProjectSelector() {
  const current = state.selectedProjectId || "all";
  els.projectSelector.innerHTML = '<option value="all">All Projects</option>';

  (state.projects || []).forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.name || p.id;
    els.projectSelector.appendChild(opt);
  });

  // Check for root issues (issues with no project_id)
  const hasRootIssues = (state.issues || []).some(
    (i) => !i.project_id && !i.project && !i.projectId,
  );
  if (hasRootIssues) {
    const opt = document.createElement("option");
    opt.value = "root";
    opt.textContent = "Root / Global";
    els.projectSelector.appendChild(opt);
  }

  els.projectSelector.value = current;
}

// Data fetching is now handled by LSP via extension events
function fetchIssues(projectId) {
  refreshAll();
}

// ----------------------------------------------------
// Creation Logic
// ----------------------------------------------------

function openCreateFlow(type, parentId = null) {
  if (!state.selectedProjectId) {
    vscode.postMessage({
      type: "INFO",
      value: "Please select a project first.",
    });
    return;
  }

  // Pre-fill form
  els.createTitle.value = "";
  els.createType.value = type;
  els.createProject.value = state.selectedProjectId;

  // Prepare Parent Options (Async) - handle parentId selection after load
  populateParentOptions(state.selectedProjectId, parentId);

  showView("view-create");
  els.createTitle.focus();
}

async function populateParentOptions(currentProjectId, preselectedId) {
  const select = els.createParent;
  select.innerHTML = '<option value="">(None)</option>';
  select.disabled = true;

  try {
    const epics = [];

    // 1. Current Project (Fast)
    const currentEpics = state.issues
      .filter((i) => i.type === "epic")
      .map((e) => ({ ...e, group: "Current Project" }));
    epics.push(...currentEpics);

    // 2. All Epics/Archs across all known projects
    const allRoots = state.issues
      .filter((i) => i.type === "epic" || i.type === "arch")
      .map((e) => {
        const p = state.projects.find((proj) => proj.id === e.project_id);
        return { ...e, group: p ? `Project: ${p.name}` : "Other" };
      });
    epics.push(...allRoots);

    // Render
    const groups = {};
    epics.forEach((e) => {
      if (!groups[e.group]) groups[e.group] = [];
      groups[e.group].push(e);
    });

    // Sort Groups: Current First
    const groupNames = Object.keys(groups).sort((a, b) => {
      if (a === "Current Project") return -1;
      if (b === "Current Project") return 1;
      return a.localeCompare(b);
    });

    groupNames.forEach((g) => {
      const optgroup = document.createElement("optgroup");
      optgroup.label = g;
      groups[g].forEach((e) => {
        const opt = document.createElement("option");
        opt.value = e.id;
        opt.textContent = `${e.id}: ${e.title}`;
        if (e.id === preselectedId) opt.selected = true;
        optgroup.appendChild(opt);
      });
      select.appendChild(optgroup);
    });

    // If preselected ID was not found (e.g. from different un-fetched project), add it manually
    if (
      preselectedId &&
      !Array.from(select.options).some((o) => o.value === preselectedId)
    ) {
      const opt = document.createElement("option");
      opt.value = preselectedId;
      opt.textContent = `${preselectedId} (Unknown)`;
      opt.selected = true;
      select.appendChild(opt);
    }
  } catch (e) {
    console.warn("Failed to populate parents", e);
  } finally {
    select.disabled = false;
  }
}

async function performCreateIssueFromForm() {
  const title = els.createTitle.value.trim();
  if (!title) return;

  const type = els.createType.value;
  const parent = els.createParent.value.trim() || null;
  const projectId = els.createProject.value;

  vscode.postMessage({
    type: "CREATE_ISSUE",
    value: {
      title,
      type: type.toLowerCase(),
      parent,
      project_id: projectId,
      status: "open",
    },
  });

  showView("view-home");
}

async function performIssueAction(issue, action) {
  vscode.postMessage({
    type: "UPDATE_ISSUE",
    issueId: issue.id,
    changes: {
      status: action.target_status || issue.status,
      stage: action.target_stage || issue.stage,
      solution: action.target_solution || issue.solution,
      project_id: state.selectedProjectId,
    },
  });
}

// ----------------------------------------------------
// Rendering Logic
// ----------------------------------------------------

function renderTree() {
  els.issueTree.innerHTML = "";
  const query = state.searchQuery || "";
  const projectId = state.selectedProjectId;

  // 1. Filter by Project
  let targetIssues = (state.issues || []).filter((i) => i && i.id);
  if (projectId && projectId !== "all") {
    if (projectId === "root") {
      // Filter for issues with NO project id
      targetIssues = targetIssues.filter(
        (i) => !i.project_id && !i.project && !i.projectId,
      );
    } else {
      const target = projectId.toLowerCase();
      targetIssues = targetIssues.filter((i) => {
        const p = (i.project_id || i.project || i.projectId || i.Project || "")
          .toString()
          .toLowerCase();
        return p === target;
      });
    }
  }

  if (targetIssues.length === 0) {
    els.issueTree.innerHTML = `<div class="empty-state">No issues to display. (Total synced: ${state.issues.length})</div>`;
    return;
  }

  // 2. Build Maps
  const idMap = new Map(targetIssues.map((i) => [i.id, i]));
  const childrenMap = new Map();
  targetIssues.forEach((i) => {
    const parentId = i.parent || i.Parent;
    if (parentId) {
      if (!childrenMap.has(parentId)) childrenMap.set(parentId, []);
      childrenMap.get(parentId).push(i);
    }
  });

  const sortFn = (a, b) => statusWeight(a.status) - statusWeight(b.status);

  function hasMatch(node) {
    if (!query) return true;
    const t = (node.title || "").toLowerCase();
    const id = (node.id || "").toLowerCase();
    return t.includes(query) || id.includes(query);
  }

  const renderInner = (issue, depth = 0) => {
    if (query && !hasMatch(issue)) return null;
    const children = (childrenMap.get(issue.id) || []).sort(sortFn);
    if (children.length > 0) {
      return createTreeNode(issue, children, depth, renderInner);
    } else {
      return createIssueItem(issue, depth);
    }
  };

  // 3. Roots Discovery
  let roots = targetIssues.filter((i) => {
    const pid = i.parent || i.Parent;
    return !pid || !idMap.has(pid);
  });

  const container = document.createDocumentFragment();
  roots.sort(sortFn).forEach((r) => {
    const node = renderInner(r);
    if (node) container.appendChild(node);
  });

  if (container.children.length === 0 && targetIssues.length > 0) {
    // If no roots (maybe circular?), just show all as flat
    targetIssues.forEach((i) => {
      const node = createIssueItem(i, 0);
      if (node) container.appendChild(node);
    });
  }

  els.issueTree.appendChild(container);
}

function statusWeight(status) {
  const map = { doing: 0, draft: 1, review: 2, backlog: 3, done: 4, closed: 5 };
  return map[status] ?? 99;
}

function createTreeNode(issue, children, depth = 0, renderInner) {
  const container = document.createElement("div");
  container.className = "tree-group";
  if (depth > 0) {
    container.style.paddingLeft = `${depth * 12}px`;
  }

  const isExpanded = state.expandedIds.has(issue.id) || !!state.searchQuery;

  if (!isExpanded) {
    container.classList.add("collapsed");
  }

  /* Header Logic */
  const header = document.createElement("div");
  header.className = "tree-group-header";

  // 1. Calculate Stats (Only immediate children)
  const stats = { done: 0, review: 0, doing: 0, draft: 0 };
  let primaryStatus = "draft"; // Derived status for the group itself

  // Logic to determine group status based on children or self
  // If self has status, use it. If not, maybe infer?
  // For Epics, usually they have their own status. Let's use issue.status/stage as primary.
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
    )
      stats.done++;
    else if (cs.includes("review")) stats.review++;
    else if (cs.includes("doing")) stats.doing++;
    else stats.draft++;
  });

  const total = children.length;
  // 3. Progress Bar Logic pre-calculation
  let barHtml = "";
  if (total > 0) {
    const pDone = (stats.done / total) * 100;
    const pReview = (stats.review / total) * 100;
    const pDoing = (stats.doing / total) * 100;
    const stop1 = pDone;
    const stop2 = pDone + pReview;
    const stop3 = pDone + pReview + pDoing;

    // We render the bar as a child of the header container, absolutely positioned at bottom
    // But we need to inject it into HTML string or append later.
    // Let's use append later to keep string clean, OR inline styles.
  }

  const type = (issue.type || "feature").toLowerCase();

  // Unified HTML Structure
  header.innerHTML = `
    <div class="card-content">
       <div class="card-left">
          <div class="chevron">${ICONS.CHEVRON}</div>
          <div class="icon type-${type}" style="margin-right: 6px;">${getIcon(issue.type)}</div>
          <div class="title" title="${escapeHtml(issue.title)}">
            <span style="color:var(--text-secondary); margin-right:6px; font-family: 'Courier New', monospace; font-size: 11px;">${escapeHtml(issue.id)}</span>
            ${escapeHtml(issue.title)}
          </div>
       </div>
       <div class="card-right">
          <!-- Count Badge -->
          ${total > 0 ? `<div class="tree-group-count">${total > 99 ? "99+" : total}</div>` : ""}
          <!-- Status Dot -->
          <div class="status-dot ${primaryStatus}" title="Status: ${s}"></div>
          <!-- Add Button -->
          <div class="item-add-btn" title="Add Sub-issue">${ICONS.PLUS}</div>
       </div>
    </div>
  `;

  // Inject Progress Bar (if needed)
  if (total > 0) {
    const pDone = (stats.done / total) * 100;
    const pReview = (stats.review / total) * 100;
    const pDoing = (stats.doing / total) * 100;
    const stop1 = pDone;
    const stop2 = pDone + pReview;
    const stop3 = pDone + pReview + pDoing;

    const bar = document.createElement("div");
    bar.className = "epic-progress-bar";
    bar.style.background = `linear-gradient(to right,
      var(--status-done) 0% ${stop1}%,
      var(--status-review) ${stop1}% ${stop2}%,
      var(--status-doing) ${stop2}% ${stop3}%,
      var(--border-color) ${stop3}% 100%
    )`;
    header.appendChild(bar);
  }

  // Wire up Add Button
  const addBtn = header.querySelector(".item-add-btn");
  addBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    openCreateFlow("feature", issue.id);
  });

  const list = document.createElement("div");
  list.className = "tree-group-list";

  // Recursive call for matching nodes
  children.forEach((child) => {
    const childNode = renderInner(child, depth + 1);
    if (childNode) list.appendChild(childNode);
  });

  // Interaction
  header.addEventListener("click", () => {
    const wasCollapsed = container.classList.contains("collapsed");
    if (wasCollapsed) {
      container.classList.remove("collapsed");
      state.expandedIds.add(issue.id);
    } else {
      container.classList.add("collapsed");
      state.expandedIds.delete(issue.id);
    }
    saveLocalState();
  });

  header.setAttribute("draggable", "true");
  header.addEventListener("dragstart", (e) => {
    e.stopPropagation();
    setupDragData(e, issue);
  });

  header.addEventListener("dblclick", (e) => {
    e.stopPropagation();
    openFile(issue);
  });

  container.appendChild(header);
  container.appendChild(list);
  return container;
}

// Tree item rendering logic

function createIssueItem(issue, depth = 0) {
  const item = document.createElement("div");
  const isDone =
    issue.stage === "done" ||
    issue.status === "closed" ||
    issue.status === "done";

  item.className = `issue-item ${isDone ? "done" : ""}`;
  item.dataset.id = issue.id;
  if (depth > 0) {
    item.style.paddingLeft = `${depth * 12 + 28}px`; // 28 is base padding for items
  }

  // Draggable Logic
  item.setAttribute("draggable", "true");
  item.addEventListener("dragstart", (e) => {
    setupDragData(e, issue);
  });

  // Status Class Mapping
  let statusClass = "draft";
  const s = (issue.stage || issue.status || "draft").toLowerCase();

  if (s.includes("doing") || s.includes("progress")) statusClass = "doing";
  else if (s.includes("review")) statusClass = "review";
  else if (s.includes("done")) statusClass = "done";
  else if (s.includes("closed")) statusClass = "closed";
  else statusClass = "draft";

  const type = (issue.type || "feature").toLowerCase();

  // HTML Construction: Left (Info) + Right (Status & Add)
  item.innerHTML = `
    <div class="card-content">
      <div class="card-left">
        <div class="icon type-${type}">${getIcon(issue.type)}</div>
        <div class="title" title="${escapeHtml(issue.title)}">
          <span style="color:var(--text-secondary); margin-right:6px; font-family: 'Courier New', monospace; font-size: 11px;">${escapeHtml(issue.id)}</span>
          ${escapeHtml(issue.title)}
        </div>
      </div>
      <div class="card-right">
         <div class="status-dot ${statusClass}" title="Status: ${s}"></div>
         <div class="item-add-btn" title="Add Sub-issue">${ICONS.PLUS}</div>
      </div>
    </div>
  `;

  // Wire up Add Button
  const addBtn = item.querySelector(".item-add-btn");
  addBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    // Defaulting to creating a 'task' if it's a leaf node, but 'feature' is safe generic default
    // or let user choose. Current openCreateFlow sets the type dropdown value.
    openCreateFlow("feature", issue.id);
  });

  // Event: Click -> Open File
  item.addEventListener("click", (e) => {
    openFile(issue);
  });

  return item;
}

function renderExecutionProfiles(profiles) {
  if (!els.executionList) return;
  els.executionList.innerHTML = "";

  if (!profiles || profiles.length === 0) {
    els.executionList.innerHTML = `<div class="empty-state" style="padding:10px;">No execution configs found.<br/>Checked ~/.monoco/execution and ./.monoco/execution</div>`;
    return;
  }

  profiles.forEach((p) => {
    const item = document.createElement("div");
    item.className = "execution-item";
    item.innerHTML = `
      <div class="exec-icon">${ICONS.EXECUTION}</div>
      <div class="exec-info">
        <div class="exec-name">${escapeHtml(p.name)}</div>
        <div class="exec-source">${p.source} • ${escapeHtml(
          p.path.split("/").pop(),
        )}</div>
      </div>
      <div class="chevron" style="transform: rotate(-90deg); opacity: 0.5;">${
        ICONS.CHEVRON
      }</div>
    `;

    item.addEventListener("click", () => {
      vscode.postMessage({ type: "OPEN_FILE", path: p.path });
    });

    els.executionList.appendChild(item);
  });
}

/**
 * Configure drag and drop data for an issue.
 * @param {DragEvent} e
 * @param {any} issue
 */
function setupDragData(e, issue) {
  const root = window.monocoConfig?.rootPath;
  let fullPath = issue.path;

  if (!fullPath) {
    // Fallback: no path available, just set plain text ID
    e.dataTransfer.setData("text/plain", issue.id);
    return;
  }

  // Check if path is absolute
  const isAbsolute = fullPath.startsWith("/") || fullPath.match(/^[a-zA-Z]:/);

  // Resolve relative path if root is available
  if (root && !isAbsolute) {
    // Handle path separators
    const sep = root.includes("\\") ? "\\" : "/";

    // Normalize separators in the relative path
    const normalizedPath = fullPath.replace(/\\/g, "/");

    // Join paths properly
    const joinedPath = root + (root.endsWith(sep) ? "" : sep) + normalizedPath;

    // Normalize the result (handle ../ and ./ )
    fullPath = joinedPath
      .split("/")
      .reduce((acc, part) => {
        if (part === "..") {
          acc.pop();
        } else if (part && part !== ".") {
          acc.push(part);
        }
        return acc;
      }, [])
      .join("/");

    // Ensure leading slash for Unix paths
    if (!fullPath.startsWith("/") && !fullPath.match(/^[a-zA-Z]:/)) {
      fullPath = "/" + fullPath;
    }
  }

  // Debug logging
  console.log(
    "[Drag] Issue:",
    issue.id,
    "Original path:",
    issue.path,
    "Resolved:",
    fullPath,
  );

  // Construct proper file:// URI with URL encoding
  // VS Code expects: file:///absolute/path (with URL encoding for special chars)
  const pathSegments = fullPath.split("/").map((segment) => {
    return encodeURIComponent(segment);
  });

  let encodedPath = pathSegments.join("/");
  let fileUri;
  if (fullPath.match(/^[a-zA-Z]:/)) {
    // Windows: file:///C:/path/to/file
    fileUri = "file:///" + encodedPath;
  } else {
    // Unix: file:///path/to/file
    fileUri = "file://" + encodedPath;
  }

  console.log("[Drag] File URI:", fileUri);

  // 1. text/uri-list - Primary for opening files
  e.dataTransfer.setData("text/uri-list", fileUri);

  // 2. text/plain - Fallback
  e.dataTransfer.setData("text/plain", fullPath);

  // 3. VS Code specific hint
  e.dataTransfer.setData("application/vnd.code.tree.monoco", fileUri);

  // Also set custom data for our internal drop handling
  e.dataTransfer.setData("application/monoco-issue", JSON.stringify(issue));
}

function openFile(issue) {
  if (!issue.path) {
    console.warn("No path for issue", issue);
  }
  vscode.postMessage({
    type: "OPEN_ISSUE_FILE",
    value: { path: issue.path, title: issue.title },
  });
}

function saveLocalState() {
  vscode.setState({
    expandedIds: Array.from(state.expandedIds),
    searchQuery: state.searchQuery,
    settings: state.settings,
  });
}

function escapeHtml(unsafe) {
  if (!unsafe) return "";
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
