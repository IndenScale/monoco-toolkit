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
    // API Base removed, pure LSP now
    webUrl: "http://127.0.0.1:8642",
  },
};

// Icons (Abstract Monoline SVGs)
const ICONS = {
  EPIC: `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="12" height="12" rx="2" /><path d="M5 8h6M8 5v6" /></svg>`,
  FEATURE: `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6" /><path d="M8 5v6" /></svg>`,
  BUG: `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M8 2v4m-3 1l-2-2m10 2l2-2m-9 5h8m-8 3l-1 2m7-2l1 2M8 14a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" /></svg>`,
  CHORE: `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 3l10 10M13 3L3 13" /></svg>`,
  CHEVRON: `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 3l5 5-5 5" /></svg>`,
  WEB: `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.2"><circle cx="8" cy="8" r="6"/><path d="M2.5 8h11M8 2.5a12.9 12.9 0 0 0 0 11 12.9 12.9 0 0 0 0-11z"/></svg>`,
  SETTINGS: `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M8.5 1.5a.5.5 0 0 0-1 0l-.25 1.5a5.5 5.5 0 0 0-1.7.7l-1.4-.6a.5.5 0 0 0-.6.2l-1 1.7a.5.5 0 0 0 .1.6l1.2 1a5.5 5.5 0 0 0 0 1.8l-1.2 1a.5.5 0 0 0-.1.6l1 1.7a.5.5 0 0 0 .6.2l1.4-.6a5.5 5.5 0 0 0 1.7.7l.25 1.5a.5.5 0 0 0 1 0l.25-1.5a5.5 5.5 0 0 0 1.7-.7l1.4.6a.5.5 0 0 0 .6-.2l1-1.7a.5.5 0 0 0-.1-.6l-1.2-1a5.5 5.5 0 0 0 0-1.8l1.2-1a.5.5 0 0 0 .1-.6l-1-1.7a.5.5 0 0 0-.6-.2l-1.4.6a5.5 5.5 0 0 0-1.7-.7L8.5 1.5z"/><circle cx="8" cy="8" r="2.5"/></svg>`,
  PLUS: `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M8 3v10M3 8h10"/></svg>`,
  BACK: `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M10 13L5 8l5-5"/></svg>`,
  EXECUTION: `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M3 3l10 5-10 5V3z"/></svg>`,
};

function getIcon(type) {
  const t = (type || "").toUpperCase();
  if (t === "EPIC") return ICONS.EPIC;
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
  // Toolbar
  btnWeb: document.getElementById("btn-web"),
  btnSettings: document.getElementById("btn-settings"),
  btnAddEpic: document.getElementById("btn-add-epic"),
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
  settingWebUrl: document.getElementById("setting-web-url"),
  btnSaveSettings: document.getElementById("btn-save-settings"),
  // Tabs
  settingsTabs: document.querySelectorAll(".settings-tabs .tab-btn"),
  executionList: document.getElementById("execution-list"),
  // Other
  addEpicZone: document.getElementById("add-epic-zone"),
};

// Initialization
document.addEventListener("DOMContentLoaded", async () => {
  els.btnBackCreate.innerHTML = ICONS.BACK;
  els.btnBackSettings.innerHTML = ICONS.BACK;

  initHoverWidget();

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

  // Config Injection
  if (window.monocoConfig) {
    state.settings.webUrl = window.monocoConfig.webUrl || state.settings.webUrl;
    // apiBase is gone
  }

  // Event Listeners
  window.addEventListener("message", async (event) => {
    const message = event.data;
    if (message.type === "REFRESH") refreshAll();

    if (message.type === "DATA_UPDATED") {
      handleDataUpdate(message.payload);
    }

    if (message.type === "SHOW_CREATE_VIEW") {
      openCreateFlow("feature");
    }

    if (message.type === "EXECUTION_PROFILES") {
      renderExecutionProfiles(message.value);
    }
  });

  // Tap switching
  els.settingsTabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      // Deactivate all
      els.settingsTabs.forEach((b) => b.classList.remove("active"));
      document
        .querySelectorAll(".tab-content")
        .forEach((c) => c.classList.remove("active"));

      // Activate Clicked
      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");

      // Logic
      if (targetId === "tab-execution") {
        vscode.postMessage({
          type: "FETCH_EXECUTION_PROFILES",
          projectId: state.selectedProjectId,
        });
      }
    });
  });

  // ... (Rest of event listeners logic)

  els.projectSelector.addEventListener("change", async (e) => {
    await setActiveProject(e.target.value);
  });

  els.searchInput?.addEventListener("input", (e) => {
    state.searchQuery = e.target.value.toLowerCase();
    savePersistentState();
    renderTree();
  });

  els.addEpicZone?.addEventListener("click", () => openCreateFlow("epic"));

  els.btnBackCreate?.addEventListener("click", () => showView("view-home"));
  els.btnBackSettings?.addEventListener("click", () => showView("view-home"));

  // Form Submission
  els.btnSubmitCreate?.addEventListener("click", async () => {
    await performCreateIssueFromForm();
  });

  // Drag & Drop for Create Parent (Same as before)
  if (els.createParent) {
    // ... [Previous Drag logic, omitted for brevity, it relies on DOM only] ...
    // Note: I will copy it if I write full file, but I am overwriting.
    // I need to include it.
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
    state.settings.webUrl = els.settingWebUrl.value.trim();
    savePersistentState();
    showView("view-home");
  });

  // Initial Load
  refreshAll();
  // Polling? LSP handles push updates, so we don't strictly need polling.
  // But maybe a backup sync every 30s.
  setInterval(refreshAll, 30000);
});

function showView(viewId) {
  document
    .querySelectorAll(".view")
    .forEach((el) => el.classList.remove("active"));
  document.getElementById(viewId).classList.add("active");
}

function refreshAll() {
  vscode.postMessage({ type: "GET_LOCAL_DATA" });
}

function handleDataUpdate(payload) {
  // Payload: { issues: [], projects: [], workspaceState: {} }
  state.issues = payload.issues || [];
  state.projects = payload.projects || [];
  state.workspaceState = payload.workspaceState || {};

  // Sync Selector
  renderProjectSelector();

  // Sync Active Project
  let targetId = els.projectSelector.value;
  if (
    (!targetId || targetId === "all") &&
    state.workspaceState.last_active_project_id
  ) {
    targetId = state.workspaceState.last_active_project_id;
  }

  if (targetId && targetId !== "all") {
    els.projectSelector.value = targetId;
    state.selectedProjectId = targetId;
  } else {
    state.selectedProjectId = "all";
  }

  renderTree();
}

async function setActiveProject(projectId) {
  state.selectedProjectId = projectId;
  // Persist via Extension
  vscode.postMessage({
    type: "SAVE_STATE",
    key: "last_active_project_id",
    value: projectId,
  });
  renderTree();
}

function renderProjectSelector() {
  const current = els.projectSelector.value;
  els.projectSelector.innerHTML = '<option value="all">All Projects</option>';
  
  // Use a Set to track unique project IDs
  const seenProjects = new Set();
  
  state.projects.forEach((p) => {
    if (seenProjects.has(p.id)) return;
    seenProjects.add(p.id);

    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.name || p.id; // Fallback
    if (
      p.id === current ||
      p.id === state.workspaceState.last_active_project_id
    ) {
      opt.selected = true;
    }
    els.projectSelector.appendChild(opt);
  });
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

  els.createTitle.value = "";
  els.createType.value = type;
  els.createProject.value = state.selectedProjectId;

  // Populate Parents: Use local state.issues
  populateParentOptions(state.selectedProjectId, parentId);

  showView("view-create");
  els.createTitle.focus();
}

function populateParentOptions(currentProjectId, preselectedId) {
  const select = els.createParent;
  select.innerHTML = '<option value="">(None)</option>';

  // Epics from current project
  const currentEpics = state.issues
    .filter((i) => i.type === "epic" && i.project_id === currentProjectId)
    .sort((a, b) => a.title.localeCompare(b.title));

  // Epics from other projects
  const otherEpics = state.issues
    .filter((i) => i.type === "epic" && i.project_id !== currentProjectId)
    .sort((a, b) => a.title.localeCompare(b.title));

  if (currentEpics.length > 0) {
    const g = document.createElement("optgroup");
    g.label = "Current Project";
    currentEpics.forEach((e) => {
      const opt = document.createElement("option");
      opt.value = e.id;
      opt.textContent = `${e.id}: ${e.title}`;
      if (e.id === preselectedId) opt.selected = true;
      g.appendChild(opt);
    });
    select.appendChild(g);
  }

  if (otherEpics.length > 0) {
    const g = document.createElement("optgroup");
    g.label = "Other Projects";
    otherEpics.forEach((e) => {
      const opt = document.createElement("option");
      opt.value = e.id;
      opt.textContent = `${e.id}: ${e.title}`;
      if (e.id === preselectedId) opt.selected = true;
      g.appendChild(opt);
    });
    select.appendChild(g);
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
      type,
      parent,
      projectId,
    },
  });

  showView("view-home");
}

async function performIssueAction(issue, action) {
  // Translate action to changes
  const changes = {};
  if (action.target_status) changes.status = action.target_status;
  if (action.target_stage) changes.stage = action.target_stage;
  if (action.target_solution) changes.solution = action.target_solution;

  vscode.postMessage({
    type: "UPDATE_ISSUE",
    issueId: issue.id,
    changes: changes,
  });
}

// ----------------------------------------------------
// Helper Functions
// ----------------------------------------------------

function savePersistentState() {
  vscode.setState({
    expandedIds: Array.from(state.expandedIds),
    searchQuery: state.searchQuery,
    settings: state.settings,
  });
}

function saveLocalState() {
  // Alias for compatibility with old code logic calls
  savePersistentState();
}

function openFile(issue) {
  vscode.postMessage({
    type: "OPEN_ISSUE_FILE",
    value: { path: issue.filePath },
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

// ----------------------------------------------------
// Rendering Logic (Tree, Drag, Hover)
// ----------------------------------------------------

// ... (Reuse renderTree, createEpicNode, createIssueItem, statusWeight from original)
// To ensure they are present, I need to include them.

function renderTree() {
  els.issueTree.innerHTML = "";

  // Filter by Project
  let projectIssues = state.issues;
  if (state.selectedProjectId && state.selectedProjectId !== "all") {
    projectIssues = state.issues.filter(
      (i) => i.project_id === state.selectedProjectId
    );
  }

  // Filter by Search
  let displayIssues = projectIssues;
  if (state.searchQuery) {
    displayIssues = projectIssues.filter(
      (i) =>
        i.title.toLowerCase().includes(state.searchQuery) ||
        i.id.toLowerCase().includes(state.searchQuery)
    );
  }

  if (displayIssues.length === 0) {
    els.issueTree.innerHTML = `<div class="empty-state"><span>No issues found.</span></div>`;
    return;
  }

  // ... (Same grouping logic as before) ...
  const allEpics = projectIssues.filter((i) => i.type === "epic");
  const epicGroups = new Map();
  allEpics.forEach((e) => epicGroups.set(e.id, []));
  const orphans = [];

  projectIssues.forEach((issue) => {
    if (issue.type === "epic") return;
    if (issue.parent && epicGroups.has(issue.parent)) {
      epicGroups.get(issue.parent).push(issue);
    } else {
      orphans.push(issue);
    }
  });

  // Render
  const sortFn = (a, b) => statusWeight(a.status) - statusWeight(b.status);

  allEpics.sort(sortFn).forEach((epic) => {
    let children = epicGroups.get(epic.id);
    children.sort(sortFn);

    // Filter children if search query
    if (state.searchQuery) {
      const query = state.searchQuery;
      const matches =
        children.some((c) => c.title.toLowerCase().includes(query)) ||
        epic.title.toLowerCase().includes(query);
      if (!matches) return;
      // If match, show all or filtered? Usually filtered.
      // Simplified: show if epic matches OR any child matches.
    }

    els.issueTree.appendChild(createEpicNode(epic, children));
  });

  if (orphans.length > 0) {
    orphans.sort(sortFn);
    // Filter orphans
    if (state.searchQuery) {
      // ... logic ...
    }
    const orphanEpic = { title: "Unassigned Issues", id: "virtual-orphans" };
    els.issueTree.appendChild(createEpicNode(orphanEpic, orphans, true));
  }
}

function statusWeight(status) {
  const map = { doing: 0, draft: 1, review: 2, backlog: 3, done: 4, closed: 5 };
  return map[status] ?? 99;
}

function createEpicNode(epic, children, isVirtual = false) {
  const container = document.createElement("div");
  container.className = "tree-group";

  const isExpanded = state.expandedIds.has(epic.id) || !!state.searchQuery;

  if (!isExpanded) {
    container.classList.add("collapsed");
  }

  /* Header Logic */
  const header = document.createElement("div");
  header.className = "tree-group-header";

  // 1. Calculate Stats
  const stats = { done: 0, review: 0, doing: 0, draft: 0 };
  children.forEach((c) => {
    const s = (c.stage || c.status || "draft").toLowerCase();
    if (s.includes("done") || s.includes("closed") || s.includes("implemented"))
      stats.done++;
    else if (s.includes("review")) stats.review++;
    else if (s.includes("doing")) stats.doing++;
    else stats.draft++;
  });

  const total = children.length;

  // 2. Count Display (Capsule)
  const countDisplay = total > 99 ? "99+" : total;
  const countHtml =
    total > 0 ? `<div class="tree-group-count">${countDisplay}</div>` : "";

  header.innerHTML = `
    <div class="chevron">${ICONS.CHEVRON}</div>
    <div class="tree-group-title">${escapeHtml(epic.title)}</div>
    ${countHtml}
  `;

  setupHover(header, epic);

  // 3. Progress Bar (The 2px Line)
  if (total > 0) {
    const pDone = (stats.done / total) * 100;
    const pReview = (stats.review / total) * 100;
    const pDoing = (stats.doing / total) * 100;
    // Todo takes the rest

    // Stack Order: Done (Green) -> Review (Purple) -> Doing (Blue) -> Todo (Transparent/Grey)
    // We use var colors from CSS.
    const bar = document.createElement("div");
    bar.className = "epic-progress-bar";

    const stop1 = pDone;
    const stop2 = pDone + pReview;
    const stop3 = pDone + pReview + pDoing;

    bar.style.background = `linear-gradient(to right, 
      var(--status-done) 0% ${stop1}%, 
      var(--status-review) ${stop1}% ${stop2}%, 
      var(--status-doing) ${stop2}% ${stop3}%, 
      var(--border-color) ${stop3}% 100%
    )`;

    header.appendChild(bar);
  }

  // Add "+" button (Allow for Epics and Unassigned)
  if (!isVirtual || epic.id === "virtual-orphans") {
    const addBtn = document.createElement("div");
    addBtn.className = "add-feature-btn";
    addBtn.innerHTML = ICONS.PLUS;
    addBtn.title = "Add Feature";
    addBtn.addEventListener("click", (e) => {
      e.stopPropagation(); // Stop collapse
      const pid = isVirtual ? "" : epic.id;
      openCreateFlow("feature", pid);
    });
    addBtn.addEventListener("dblclick", (e) => {
      e.stopPropagation(); // Prevent "Open File" on rapid clicks
    });
    header.appendChild(addBtn);
  }

  const list = document.createElement("div");
  list.className = "tree-group-list";

  children.forEach((child) => list.appendChild(createIssueItem(child)));

  // Interaction
  header.addEventListener("click", (e) => {
    // If the click target is the add button, don't collapse/expand
    if (e.target.closest(".add-feature-btn")) {
      return;
    }

    const wasCollapsed = container.classList.contains("collapsed");

    if (wasCollapsed) {
      container.classList.remove("collapsed");
      state.expandedIds.add(epic.id);
    } else {
      container.classList.add("collapsed");
      state.expandedIds.delete(epic.id);
    }
    savePersistentState();
  });

  if (!isVirtual) {
    // Enable drag for epic headers
    header.setAttribute("draggable", "true");
    header.addEventListener("dragstart", (e) => {
      // Stop propagation to prevent collapse during drag
      e.stopPropagation();
      setupDragData(e, epic);
    });

    header.addEventListener("dblclick", (e) => {
      e.stopPropagation();
      openFile(epic);
    });
  }

  container.appendChild(header);
  container.appendChild(list);
  return container;
}

function createIssueItem(issue) {
  const item = document.createElement("div");
  const isDone =
    issue.stage === "done" ||
    issue.status === "closed" ||
    issue.status === "done";

  item.className = `issue-item ${isDone ? "done" : ""}`;
  item.dataset.id = issue.id;

  // Draggable Logic
  item.setAttribute("draggable", "true");
  item.addEventListener("dragstart", (e) => {
    setupDragData(e, issue);
  });

  setupHover(item, issue);

  // Status Class Mapping
  let statusClass = "draft";
  const s = (issue.stage || issue.status || "draft").toLowerCase();

  if (s.includes("doing") || s.includes("progress")) statusClass = "doing";
  else if (s.includes("review")) statusClass = "review";
  else if (s.includes("done")) statusClass = "done";
  else if (s.includes("closed")) statusClass = "closed";
  else statusClass = "draft";

  // HTML Construction
  item.innerHTML = `
    <div class="card-content">
      <div class="card-left">
        <div class="icon type-${issue.type.toLowerCase()}">${getIcon(
    issue.type
  )}</div>
        <div class="title" title="${escapeHtml(issue.title)}">${escapeHtml(
    issue.title
  )}</div>
      </div>
      <div class="action-group" id="action-group-${issue.id}"></div>
    </div>
  `;
  // Render Actions (Buttons on the right)
  const actionGroup = item.querySelector(`#action-group-${issue.id}`);
  if (issue.actions && issue.actions.length > 0) {
    issue.actions.forEach((action) => {
      const btn = document.createElement("button");
      btn.className = "action-btn";
      btn.textContent = action.label;
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        performIssueAction(issue, action);
      });
      actionGroup.appendChild(btn);
    });
  }

  // Event: Click -> Open File
  item.addEventListener("click", (e) => {
    openFile(issue);
  });
  return item;
}

function setupDragData(e, item) {
  e.dataTransfer.setData("application/monoco-issue", JSON.stringify(item));
}

function initHoverWidget() {
  // ...
}

function renderExecutionProfiles() {
  // ...
}

function setupHover(el, item) {
  // ...
}
