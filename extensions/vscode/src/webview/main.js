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

// Icons (Abstract Monoline SVGs)
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

/**
 * Get SVG icon for a given issue type.
 * @param {string} type
 * @returns {string} The SVG string.
 */
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
  settingApiBase: document.getElementById("setting-api-base"),
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
  // Init Toolbar Icons
  els.btnWeb.innerHTML = ICONS.WEB;
  els.btnSettings.innerHTML = ICONS.SETTINGS;
  els.btnAddEpic.innerHTML = ICONS.PLUS;
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

  // Config Injection (Overrides saved settings if provided by extension)
  if (window.monocoConfig) {
    state.settings.apiBase =
      window.monocoConfig.apiBase || state.settings.apiBase;
    state.settings.webUrl = window.monocoConfig.webUrl || state.settings.webUrl;
  }

  // Event Listeners
  window.addEventListener("message", async (event) => {
    const message = event.data;
    if (message.type === "REFRESH") refreshAll();
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
        vscode.postMessage({ type: "FETCH_EXECUTION_PROFILES" });
      }
    });
  });

  // ... (Rest of event listeners logic)

  els.projectSelector.addEventListener("change", async (e) => {
    await setActiveProject(e.target.value);
  });

  els.searchInput?.addEventListener("input", (e) => {
    state.searchQuery = e.target.value.toLowerCase();
    saveLocalState();
    renderTree();
  });

  // Navigation
  els.btnWeb?.addEventListener("click", () => {
    // vscode.postMessage({ type: "OPEN_WEBUI" });
    // User might want to configure this URL now
    vscode.postMessage({ type: "OPEN_URL", url: state.settings.webUrl });
  });

  els.btnSettings?.addEventListener("click", () => {
    // Fill form
    els.settingApiBase.value = state.settings.apiBase;
    els.settingWebUrl.value = state.settings.webUrl;
    showView("view-settings");
  });

  els.btnAddEpic?.addEventListener("click", () => openCreateFlow("epic"));
  els.addEpicZone?.addEventListener("click", () => openCreateFlow("epic"));

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
    showView("view-home");
  });

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
  await Promise.all([fetchProjects(), fetchWorkspaceState()]);

  // Logic to sync selector with state
  let targetId = els.projectSelector.value;
  if (
    (!targetId || targetId === "all") &&
    state.workspaceState.last_active_project_id
  ) {
    targetId = state.workspaceState.last_active_project_id;
  }
  if (!targetId && state.projects.length > 0) {
    targetId = state.projects[0].id;
  }

  if (targetId) {
    els.projectSelector.value = targetId;
    state.selectedProjectId = targetId;
    await fetchIssues(targetId);
  }
}

async function fetchProjects() {
  try {
    const res = await fetch(`${state.settings.apiBase}/projects`);
    if (!res.ok) throw new Error("Failed to fetch projects");
    state.projects = await res.json();
    renderProjectSelector();
  } catch (e) {
    console.error(e);
  }
}

async function fetchWorkspaceState() {
  try {
    const res = await fetch(`${state.settings.apiBase}/workspace/state`);
    if (res.ok) {
      state.workspaceState = await res.json();
    }
  } catch (e) {
    console.error(e);
  }
}

async function setActiveProject(projectId) {
  state.selectedProjectId = projectId;
  // Persist
  try {
    await fetch(`${state.settings.apiBase}/workspace/state`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ last_active_project_id: projectId }),
    });
  } catch (e) {
    console.error("Failed to save state", e);
  }

  await fetchIssues(projectId);
}

function renderProjectSelector() {
  const current = els.projectSelector.value;
  els.projectSelector.innerHTML = "";
  state.projects.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.name;
    if (
      p.id === current ||
      p.id === state.workspaceState.last_active_project_id
    ) {
      opt.selected = true;
    }
    els.projectSelector.appendChild(opt);
  });
}

async function fetchIssues(projectId) {
  try {
    const res = await fetch(
      `${state.settings.apiBase}/issues?project_id=${projectId}`
    );
    if (!res.ok) throw new Error("Failed to fetch issues");
    state.issues = await res.json();
    renderTree();
  } catch (err) {
    els.issueTree.innerHTML = `<div class="error-state">Failed to connect to Monoco Server.</div>`;
  }
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

    // 2. Fetch Others (Async)
    const otherProjects = state.projects.filter(
      (p) => p.id !== currentProjectId
    );
    if (otherProjects.length > 0) {
      // Limit to 5 projects to prevent perf issues
      const targets = otherProjects.slice(0, 5);
      const promises = targets.map((p) =>
        fetch(`${state.settings.apiBase}/issues?project_id=${p.id}`)
          .then((r) => (r.ok ? r.json() : []))
          .then((issues) =>
            issues
              .filter((i) => i.type === "epic")
              .map((e) => ({ ...e, group: `Project: ${p.name}` }))
          )
          .catch(() => [])
      );
      const remoteEpics = (await Promise.all(promises)).flat();
      epics.push(...remoteEpics);
    }

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

  // Disable button or show loading state? (Skip for now, just await)

  try {
    const payload = {
      title,
      type: type.toLowerCase(),
      parent,
      project_id: projectId,
      status: "open",
    };

    const res = await fetch(`${state.settings.apiBase}/issues`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error(await res.text());

    // Refresh & Return
    await fetchIssues(projectId);
    showView("view-home");
  } catch (e) {
    vscode.postMessage({
      type: "INFO",
      value: "Failed to create issue: " + e.message,
    });
  }
}

async function toggleIssueStatus(issue) {
  // Logic: Draft -> Doing -> Review -> Done (Closed)
  // Map current stage or status to next
  const currentStage = (issue.stage || "draft").toLowerCase();
  let nextStage = null;
  let nextStatus = "open";
  let solution = null;

  if (issue.status === "closed") {
    // Reopen?
    nextStatus = "open";
    nextStage = "draft";
  } else {
    if (currentStage === "draft") nextStage = "doing";
    else if (currentStage === "doing") nextStage = "review";
    else if (currentStage === "review") {
      nextStatus = "closed";
      nextStage = "done";
      solution = "implemented";
    } else {
      // Default reset
      nextStage = "draft";
    }
  }

  try {
    const res = await fetch(`${state.settings.apiBase}/issues/${issue.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        status: nextStatus,
        stage: nextStage,
        solution: solution,
        project_id: state.selectedProjectId,
      }),
    });
    if (!res.ok) {
      const err = await res.json();
      vscode.postMessage({
        type: "INFO",
        value: err.detail || "Update failed",
      });
    } else {
      await fetchIssues(state.selectedProjectId);
    }
  } catch (e) {
    console.error(e);
  }
}

// ----------------------------------------------------
// Rendering Logic
// ----------------------------------------------------

function renderTree() {
  els.issueTree.innerHTML = "";

  // Filter by Search
  let displayIssues = state.issues;
  if (state.searchQuery) {
    displayIssues = state.issues.filter(
      (i) =>
        i.title.toLowerCase().includes(state.searchQuery) ||
        i.id.toLowerCase().includes(state.searchQuery)
    );
  }

  if (displayIssues.length === 0) {
    if (state.issues.length === 0) {
      els.issueTree.innerHTML = `<div class="empty-state">
        <span>No issues found.</span>
        </div>`;
    } else {
      els.issueTree.innerHTML = `<div class="empty-state">
        <span>No matches.</span>
        </div>`;
    }
    return;
  }

  const epics = displayIssues.filter((i) => i.type === "epic");
  // Note: if search is active, we might miss the epic of a matching child.
  // For simplicity, we just render flat matches OR matched structure.
  // Let's stick to the existing structure but only show matching children.

  // Actually, standard Search behavior: Show hierarchy if child matches.
  // Re-build hierarchy from FULL list, then filter nodes.

  const allEpics = state.issues.filter((i) => i.type === "epic");
  const epicMap = new Map(allEpics.map((e) => [e.id, e]));
  const epicGroups = new Map();
  allEpics.forEach((e) => epicGroups.set(e.id, []));

  const orphans = [];

  state.issues.forEach((issue) => {
    if (issue.type === "epic") return;
    if (issue.parent && epicGroups.has(issue.parent)) {
      epicGroups.get(issue.parent).push(issue);
    } else {
      orphans.push(issue);
    }
  });

  // Apply Filter to Groups
  const query = state.searchQuery;
  const filteredEpics = [];

  allEpics.forEach((epic) => {
    let children = epicGroups.get(epic.id);
    if (query) {
      children = children.filter(
        (c) =>
          c.title.toLowerCase().includes(query) ||
          c.id.toLowerCase().includes(query)
      );
    }
    // If epic matches or children match
    if (
      children.length > 0 ||
      epic.title.toLowerCase().includes(query) ||
      epic.id.toLowerCase().includes(query)
    ) {
      filteredEpics.push({ epic, children });
    }
  });

  const filteredOrphans = query
    ? orphans.filter(
        (c) =>
          c.title.toLowerCase().includes(query) ||
          c.id.toLowerCase().includes(query)
      )
    : orphans;

  // Helper Sort
  const sortFn = (a, b) => statusWeight(a.status) - statusWeight(b.status);

  // Render Epics
  filteredEpics.forEach(({ epic, children }) => {
    children.sort(sortFn);
    els.issueTree.appendChild(createEpicNode(epic, children));
  });

  // Render Orphans
  if (filteredOrphans.length > 0) {
    filteredOrphans.sort(sortFn);
    // Virtual 'Epic' for orphans
    const orphanEpic = { title: "Unassigned Issues", id: "virtual-orphans" };
    els.issueTree.appendChild(
      createEpicNode(orphanEpic, filteredOrphans, true)
    );
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
  // Auto expand on search

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

    // Construct Gradient
    // Stops:
    // Green: 0% -> pDone%
    // Purple: pDone% -> (pDone+pReview)%
    // Blue: (pDone+pReview)% -> (pDone+pReview+pDoing)%
    // Grey: (pDone+pReview+pDoing)% -> 100%

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
    addBtn.innerHTML = ICONS.PLUS; // Use SVG here too
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
  header.addEventListener("click", () => {
    const wasCollapsed = container.classList.contains("collapsed");

    if (wasCollapsed) {
      container.classList.remove("collapsed");
      state.expandedIds.add(epic.id);
    } else {
      container.classList.add("collapsed");
      state.expandedIds.delete(epic.id);
    }
    saveLocalState();
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
    <div class="icon type-${issue.type.toLowerCase()}">${getIcon(
    issue.type
  )}</div>
    <div class="title" title="${escapeHtml(issue.title)}">${escapeHtml(
    issue.title
  )}</div>
    <div class="status-light ${statusClass}" title="${
    issue.stage || issue.status
  } (Click to Advance)"></div>
  `;

  // Status Click
  const light = item.querySelector(".status-light");
  light.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleIssueStatus(issue);
  });

  // Event: Click -> Open File
  item.addEventListener("click", (e) => {
    e.stopPropagation(); // Prevent opening if clicking light? No, light propagation stopped.
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
      p.path.split("/").pop()
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
    fullPath
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

// ----------------------------------------------------
// Hover Logic
// ----------------------------------------------------

let hoverTimer = null;
let hoverWidget = null;
const HOVER_DELAY = 600;

function initHoverWidget() {
  hoverWidget = document.createElement("div");
  hoverWidget.className = "hover-widget";
  document.body.appendChild(hoverWidget);
}

function setupHover(element, issue) {
  element.addEventListener("mouseenter", (e) => {
    clearTimeout(hoverTimer);
    hoverTimer = setTimeout(() => showHover(element, issue), HOVER_DELAY);
  });

  element.addEventListener("mouseleave", () => {
    clearTimeout(hoverTimer);
    hideHover();
  });

  // Hide on click to avoid obstruction
  element.addEventListener("mousedown", () => {
    clearTimeout(hoverTimer);
    hideHover();
  });
}

async function showHover(target, issue) {
  try {
    // Check cache or fetch? For now fetch always to be fresh
    const res = await fetch(`${state.settings.apiBase}/issues/${issue.id}`);
    if (!res.ok) return;
    const detail = await res.json();

    renderHover(detail);
    positionHover(target);

    // Fade in
    requestAnimationFrame(() => {
      hoverWidget.classList.add("visible");
    });
  } catch (e) {
    // Silent fail
  }
}

function hideHover() {
  if (hoverWidget) {
    hoverWidget.classList.remove("visible");
  }
}

function renderHover(detail) {
  const icon = getIcon(detail.type);
  const status = detail.stage || detail.status;
  let bodyText = (detail.body || "").trim();

  // Remove Markdown headers for clearer preview? Or just let standard font handle it.
  // Strip first # Title if it duplicates
  bodyText = bodyText.replace(/^#\s+.*$/m, "").trim();

  hoverWidget.innerHTML = `
        <div class="hover-header">
            <div class="hover-type-icon type-${detail.type}">${icon}</div>
            <div class="hover-title-group">
                <div class="hover-title">${escapeHtml(detail.title)}</div>
                <div class="hover-id">${detail.id}</div>
            </div>
            <div class="hover-status-badge">${status}</div>
        </div>
        <div class="hover-body">${escapeHtml(bodyText)}</div>
        <div class="hover-footer">
             ${(detail.tags || [])
               .map((t) => `<span class="hover-tag">#${t}</span>`)
               .join("")}
             <span class="hover-tag" style="margin-left:auto; opacity:0.7">Click to Open</span>
        </div>
    `;
}

function positionHover(target) {
  const rect = target.getBoundingClientRect();
  const widgetRect = hoverWidget.getBoundingClientRect();

  // 1. Try Right Side
  let left = rect.right + 10;
  let top = rect.top;

  // 2. Check Horizontal Overflow (Sidebar Boundary)
  // If moving right pushes it out, or if it's too wide
  if (left + widgetRect.width > window.innerWidth - 10) {
    // Strategy: Move to Bottom, Left-Aligned (with safe padding)
    left = 10;
    top = rect.bottom + 4;
  }

  // 3. Check Vertical Overflow
  if (top + widgetRect.height > window.innerHeight - 10) {
    // If bottom clips, try shifting UP
    // If we are in "Bottom" mode (left=10), move it ABOVE the element
    if (left === 10) {
      top = rect.top - widgetRect.height - 4;
    } else {
      // If we are in "Right" mode, just clamp to bottom
      top = window.innerHeight - widgetRect.height - 10;
    }
  }

  hoverWidget.style.top = `${top}px`;
  hoverWidget.style.left = `${left}px`;
}
