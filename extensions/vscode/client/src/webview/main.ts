/**
 * Main entry point for the webview UI
 * Initializes state management, components, and message handling
 */

import { StateManager, AppState } from "./ui/state/StateManager";
import { VSCodeBridge } from "./ui/services/VSCodeBridge";
import { IssueTree } from "./ui/components/IssueTree";
import { ProjectSelector } from "./ui/components/ProjectSelector";
import { CreateForm } from "./ui/components/CreateForm";
import { ICONS } from "./ui/utils/helpers";

// View management
function showView(viewId: string) {
  document
    .querySelectorAll(".view")
    .forEach((el) => el.classList.remove("active"));
  document.getElementById(viewId)?.classList.add("active");
}

function toggleSettings(force?: boolean) {
  const settingsView = document.getElementById("view-settings");
  const primaryViews = document.getElementById("primary-views");
  const chevron = document.getElementById("settings-chevron");
  if (!settingsView || !primaryViews) {
    return;
  }

  const isCurrentlyExpanded = settingsView.classList.contains("expanded");
  const targetExpanded = force !== undefined ? force : !isCurrentlyExpanded;

  if (targetExpanded) {
    settingsView.classList.add("expanded");
    // primaryViews.classList.add("collapsed"); // Optional: if we want to shrink main view
    if (chevron) {
      (chevron as HTMLElement).style.transform = "rotate(90deg)";
    }
  } else {
    settingsView.classList.remove("expanded");
    // primaryViews.classList.remove("collapsed");
    if (chevron) {
      (chevron as HTMLElement).style.transform = "rotate(0deg)";
    }
  }
}

function toggleFilters(force?: boolean) {
  const filtersView = document.getElementById("view-filters");
  const chevron = document.getElementById("filters-chevron");
  const btnFilter = document.getElementById("btn-filter");
  if (!filtersView) {
    return;
  }

  const isCurrentlyExpanded = filtersView.classList.contains("expanded");
  const targetExpanded = force !== undefined ? force : !isCurrentlyExpanded;

  if (targetExpanded) {
    filtersView.classList.add("expanded");
    if (chevron) {
      (chevron as HTMLElement).style.transform = "rotate(90deg)";
    }
    if (btnFilter) {
      btnFilter.classList.add("active");
    }
  } else {
    filtersView.classList.remove("expanded");
    if (chevron) {
      (chevron as HTMLElement).style.transform = "rotate(0deg)";
    }
    if (btnFilter) {
      btnFilter.classList.remove("active");
    }
  }
}

// Initialization
document.addEventListener("DOMContentLoaded", async () => {
  console.log("[Webview] Initializing...");

  // 1. Initialize state manager
  const stateManager = new StateManager();
  stateManager.loadFromStorage();

  // 2. Initialize VSCode bridge
  const bridge = new VSCodeBridge(stateManager);

  // 3. Setup message handlers
  bridge.on("DATA_UPDATED", (payload) => {
    console.log("[Webview] DATA_UPDATED received");
    stateManager.setState({
      issues: payload.issues || [],
      projects: payload.projects || [],
      selectedProjectId:
        payload.workspaceState?.last_active_project_id ||
        stateManager.getState().selectedProjectId ||
        "all",
      workspaceState: payload.workspaceState || {},
    });
  });

  bridge.on("REFRESH", () => {
    console.log("[Webview] REFRESH received");
    bridge.getLocalData();
  });

  bridge.on("SHOW_CREATE_VIEW", (value) => {
    console.log("[Webview] SHOW_CREATE_VIEW received", value);
    const createForm = (window as any).__createForm as CreateForm;
    if (createForm) {
      // If value is provided, pre-fill. If not, just open.
      if (value) {
        createForm.open(value.type, value.parent);
      } else {
        createForm.open(); // Reset defaults
      }
      showView("view-create");
    }
  });

  bridge.on("SHOW_SETTINGS", () => {
    console.log("[Webview] SHOW_SETTINGS received");
    toggleSettings();
  });

  bridge.on("AGENT_STATE_UPDATED", (payload) => {
    console.log("[Webview] AGENT_STATE_UPDATED received", payload);
    stateManager.updateField("availableProviders", payload.providers);
  });

  // 4. Initialize components
  const issueTreeContainer = document.getElementById("issue-tree");
  const projectSelectorElement = document.getElementById(
    "project-selector",
  ) as HTMLElement;
  const createViewContainer = document.getElementById("view-create");

  if (!issueTreeContainer || !projectSelectorElement || !createViewContainer) {
    console.error("[Webview] Required DOM elements not found");
    return;
  }

  // Initialize components (keep references to prevent garbage collection)
  const issueTree = new IssueTree(issueTreeContainer, stateManager, bridge);
  const projectSelector = new ProjectSelector(
    projectSelectorElement,
    stateManager,
    bridge,
  );
  const createForm = new CreateForm(createViewContainer, stateManager, bridge);

  // Prevent tree-shaking
  void issueTree;
  void projectSelector;

  // Store createForm globally for message handler access
  (window as any).__createForm = createForm;

  // 5. Setup search input
  const searchInput = document.getElementById(
    "search-input",
  ) as HTMLInputElement;
  if (searchInput) {
    // Restore search query
    const state = stateManager.getState();
    searchInput.value = state.searchQuery;

    searchInput.addEventListener("input", (e) => {
      const target = e.target as HTMLInputElement;
      stateManager.updateField("searchQuery", target.value.toLowerCase());
      stateManager.saveToStorage();
    });
  }

  // 6. Setup navigation buttons
  const btnBackCreate = document.getElementById("btn-back-create");

  if (btnBackCreate) {
    btnBackCreate.addEventListener("click", () => showView("view-home"));
    btnBackCreate.innerHTML = ICONS.BACK;
  }

  // 6.b Setup settings toggle
  const settingsHeader = document.getElementById("settings-toggle-btn");
  if (settingsHeader) {
    settingsHeader.addEventListener("click", () => toggleSettings());
  }

  // 6.c Setup filters toggle
  const filtersHeader = document.getElementById("filters-toggle-btn");
  if (filtersHeader) {
    filtersHeader.addEventListener("click", () => toggleFilters());
  }

  // 6.d Setup Settings Tabs
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetTab = (btn as HTMLElement).dataset.tab;
      tabBtns.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      document.getElementById(targetTab!)?.classList.add("active");
    });
  });

  // 7. Setup settings form
  const settingDisplayId = document.getElementById(
    "setting-display-id",
  ) as HTMLInputElement;
  const settingAgentResearch = document.getElementById(
    "setting-agent-research",
  ) as HTMLSelectElement;
  const settingAgentImplementation = document.getElementById(
    "setting-agent-implementation",
  ) as HTMLSelectElement;
  const settingAgentReview = document.getElementById(
    "setting-agent-review",
  ) as HTMLSelectElement;
  const settingAgentDefault = document.getElementById(
    "setting-agent-default",
  ) as HTMLSelectElement;
  const btnSaveSettings = document.getElementById("btn-save-settings");

  // 7.b Setup environment copy
  document.querySelectorAll(".command-box").forEach((box) => {
    box.addEventListener("click", () => {
      const code = box.querySelector("code")?.textContent;
      if (code) {
        navigator.clipboard.writeText(code);
        const originalBg = (box as HTMLElement).style.backgroundColor;
        (box as HTMLElement).style.backgroundColor =
          "var(--vscode-debugIcon-breakpointForeground)";
        setTimeout(() => {
          (box as HTMLElement).style.backgroundColor = originalBg;
        }, 500);
      }
    });
  });

  const updateAgentOptions = (state: Readonly<AppState>) => {
    const providers = state.availableProviders || [];
    const selects = [
      { el: settingAgentDefault, isDefault: true },
      { el: settingAgentResearch, isDefault: false },
      { el: settingAgentImplementation, isDefault: false },
      { el: settingAgentReview, isDefault: false },
    ];

    const defaultProvider =
      settingAgentDefault?.value ||
      state.settings?.agents?.default ||
      providers[0] ||
      "";

    selects.forEach(({ el, isDefault }) => {
      if (!el) {
        return;
      }
      const currentValue = el.value;
      el.innerHTML = "";

      if (isDefault) {
        // Default agent must be a real provider if available
        if (providers.length === 0) {
          const noneOpt = document.createElement("option");
          noneOpt.value = "";
          noneOpt.textContent = "(No Providers Available)";
          el.appendChild(noneOpt);
        }
      } else {
        // Specialized agents can inherit
        const inheritOpt = document.createElement("option");
        inheritOpt.value = "";
        const defaultLabel = defaultProvider ? ` (${defaultProvider})` : "";
        inheritOpt.textContent = `Inherit from Default${defaultLabel}`;
        el.appendChild(inheritOpt);
      }

      providers.forEach((p: string) => {
        const opt = document.createElement("option");
        opt.value = p;
        opt.textContent = p.charAt(0).toUpperCase() + p.slice(1);
        el.appendChild(opt);
      });

      // Restore value or auto-select if empty and mandatory (for Default)
      if (isDefault && !currentValue && providers.length > 0) {
        el.value = providers[0];
      } else {
        el.value = currentValue;
      }
    });
  };

  // Add change listener to Default Agent to trigger label updates in others
  if (settingAgentDefault) {
    settingAgentDefault.addEventListener("change", () => {
      updateAgentOptions(stateManager.getState());
    });
  }

  if (
    settingDisplayId &&
    settingAgentResearch &&
    settingAgentImplementation &&
    settingAgentReview &&
    settingAgentDefault &&
    btnSaveSettings
  ) {
    // Load current settings
    const state = stateManager.getState();
    updateAgentOptions(state);

    if (state.settings?.ui) {
      settingDisplayId.checked = state.settings.ui.displayId;
    }
    if (state.settings?.agents) {
      settingAgentResearch.value = state.settings.agents.research;
      settingAgentImplementation.value = state.settings.agents.implementation;
      settingAgentReview.value = state.settings.agents.review;
      settingAgentDefault.value = state.settings.agents.default;
    }

    // Subscribe to update options when availableProviders change
    stateManager.subscribe((newState) => {
      updateAgentOptions(newState);
    });

    btnSaveSettings.addEventListener("click", () => {
      const agents = {
        research: settingAgentResearch.value,
        implementation: settingAgentImplementation.value,
        review: settingAgentReview.value,
        default: settingAgentDefault.value,
      };
      const ui = {
        displayId: settingDisplayId.checked,
      };

      stateManager.setState({
        settings: {
          agents,
          ui,
        },
      });
      stateManager.saveToStorage();

      // Persist to monoco config via bridge (CLI)
      const agentKeys: Record<string, string> = {
        research: "agent.providers.research",
        implementation: "agent.providers.implementation",
        review: "agent.providers.review",
        default: "agent.providers.default",
      };

      Object.entries(agentKeys).forEach(([prop, configKey]) => {
        const value = (agents as any)[prop];
        bridge.send({
          type: "UPDATE_CONFIG",
          value: { key: configKey, value: value },
        });
      });

      bridge.getLocalData(); // Reload
      toggleSettings(false); // Collapse
    });
  }

  // 8. Config injection (from extension) - Agents are usually project/global level
  if ((window as any).monocoConfig) {
    // Optional: Sync from config injection if needed
  }

  // 9. Initial data load
  console.log("[Webview] Requesting initial data...");
  try {
    await bridge.getLocalData();
  } catch (err) {
    console.error("[Webview] Failed initial data load", err);
  }

  // 10. Setup Filter View
  const btnFilter = document.getElementById("btn-filter");
  const filterContainer = document.getElementById("filter-container");

  // Toggles (Status & Stage)
  const statusToggles = document.querySelectorAll(".status-toggle");
  const stageToggles = document.querySelectorAll(".stage-toggle");

  // Tag Inputs
  const tagsInclude = document.getElementById(
    "filter-tags-include",
  ) as HTMLInputElement;
  const tagsExclude = document.getElementById(
    "filter-tags-exclude",
  ) as HTMLInputElement;
  const tagsNice = document.getElementById(
    "filter-tags-nice",
  ) as HTMLInputElement;

  // Initial State Load for Filters
  const loadFiltersToUI = () => {
    let state = stateManager.getState();

    // Auto-Migrate/Reset Filters if legacy values detected
    const fStatus = state.filters.status || [];
    const validStatus = ["open", "closed", "backlog"];
    const hasInvalidStatus = fStatus.some((s) => !validStatus.includes(s));

    if (hasInvalidStatus) {
      console.warn("[Webview] Detected legacy status filters, resetting...");
      stateManager.updateField("filters", {
        status: [],
        stage: [],
        tags: { include: [], exclude: [], nice: [] },
      });
      stateManager.saveToStorage();
      state = stateManager.getState();
    }

    const currentStatus = state.filters.status || [];
    const fStage = state.filters.stage || [];
    const fTags = state.filters.tags || { include: [], exclude: [], nice: [] };

    // Status Buttons
    statusToggles.forEach((el) => {
      const val = (el as any).dataset.value;
      if (currentStatus.includes(val)) {
        el.classList.add("active");
      } else {
        el.classList.remove("active");
      }
    });

    // Stage Buttons
    stageToggles.forEach((el) => {
      const val = (el as any).dataset.value;
      if (fStage.includes(val)) {
        el.classList.add("active");
      } else {
        el.classList.remove("active");
      }
    });

    // Tag Inputs
    if (tagsInclude) {
      tagsInclude.value = (fTags.include || []).join(", ");
    }
    if (tagsExclude) {
      tagsExclude.value = (fTags.exclude || []).join(", ");
    }
    if (tagsNice) {
      tagsNice.value = (fTags.nice || []).join(", ");
    }
  };

  // Trigger Filter Update
  const updateFiltersFromUI = () => {
    // Read Status
    const fStatus: string[] = [];
    statusToggles.forEach((el) => {
      if (el.classList.contains("active")) {
        fStatus.push((el as any).dataset.value);
      }
    });

    // Read Stage
    const fStage: string[] = [];
    stageToggles.forEach((el) => {
      if (el.classList.contains("active")) {
        fStage.push((el as any).dataset.value);
      }
    });

    // Read Tags
    const parseTags = (val: string) =>
      val
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

    const fTags = {
      include: parseTags(tagsInclude?.value || ""),
      exclude: parseTags(tagsExclude?.value || ""),
      nice: parseTags(tagsNice?.value || ""),
    };

    stateManager.updateField("filters", {
      status: fStatus,
      stage: fStage,
      tags: fTags,
    });
    stateManager.saveToStorage();
  };

  if (btnFilter && filterContainer) {
    btnFilter.innerHTML = ICONS.FILTER || "F"; // Use the icon

    // Toggle Logic
    btnFilter.addEventListener("click", () => {
      toggleFilters();
    });

    // Load initial UI state if not hidden (or just eager load)
    loadFiltersToUI();
  }

  // Bind Status Toggles
  statusToggles.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const target = e.currentTarget as HTMLElement;
      target.classList.toggle("active");
      updateFiltersFromUI();
    });
  });

  // Bind Stage Toggles
  stageToggles.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const target = e.currentTarget as HTMLElement;
      target.classList.toggle("active");
      updateFiltersFromUI();
    });
  });

  // Bind Tag Inputs (Input event for live filtering)
  [tagsInclude, tagsExclude, tagsNice].forEach((input) => {
    if (input) {
      input.addEventListener("input", () => {
        updateFiltersFromUI();
      });
    }
  });

  // 11. Data Fetching Strategy
  // Initial rapid retry to ensure data loads quickly on startup
  const fetchLocalData = () => bridge.getLocalData();

  fetchLocalData(); // Immediate
  setTimeout(fetchLocalData, 1000); // T+1s
  setTimeout(fetchLocalData, 3000); // T+3s

  // Periodic refresh
  setInterval(fetchLocalData, 10000);

  console.log("[Webview] Initialization complete");
});
