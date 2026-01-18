import { StateManager } from "../state/StateManager";
import { VSCodeBridge } from "../services/VSCodeBridge";
import { Project } from "@shared/types/Project";

/**
 * Project selector component (Custom Dropdown)
 */
export class ProjectSelector {
  private trigger: HTMLElement;
  private dropdown: HTMLElement;
  private valueDisplay: HTMLElement;

  constructor(
    private container: HTMLElement,
    private stateManager: StateManager,
    private bridge: VSCodeBridge,
  ) {
    this.trigger = this.container.querySelector(
      "#project-selector-trigger",
    ) as HTMLElement;
    this.dropdown = this.container.querySelector(
      "#project-selector-dropdown",
    ) as HTMLElement;
    this.valueDisplay = this.container.querySelector(
      "#project-selector-value",
    ) as HTMLElement;

    this.setupInteractions();

    // Subscribe to state changes
    this.stateManager.subscribe((state) =>
      this.render(state.projects, state.selectedProjectId),
    );
  }

  private setupInteractions() {
    // Toggle dropdown
    this.trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      this.container.classList.toggle("open");
    });

    // Close on click outside
    document.addEventListener("click", (e) => {
      if (!this.container.contains(e.target as Node)) {
        this.container.classList.remove("open");
      }
    });
  }

  /**
   * Render project options
   */
  render(projects: Project[], selectedProjectId: string | null) {
    const currentId = selectedProjectId || "all";
    this.dropdown.innerHTML = "";

    // "All Projects" Option
    this.addOption("all", "All Projects", currentId === "all");

    // Project Options
    projects.forEach((p) => {
      this.addOption(p.id, p.name || p.id, currentId === p.id);
    });

    // Update Display Text
    const selectedProject = projects.find((p) => p.id === currentId);
    const displayText =
      currentId === "all"
        ? "All Projects"
        : selectedProject?.name || selectedProject?.id || "Unknown Project";

    if (this.valueDisplay) {
      this.valueDisplay.textContent = displayText;
    }
  }

  private addOption(value: string, label: string, isSelected: boolean) {
    const opt = document.createElement("div");
    opt.className = "select-option";
    if (isSelected) {
      opt.classList.add("selected");
    }
    opt.textContent = label;
    opt.dataset.value = value;

    opt.addEventListener("click", async (e) => {
      e.stopPropagation();
      this.container.classList.remove("open");
      await this.bridge.setActiveProject(value);
    });

    this.dropdown.appendChild(opt);
  }
}
