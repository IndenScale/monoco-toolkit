import { StateManager } from "../state/StateManager";
import { VSCodeBridge } from "../services/VSCodeBridge";
import { Project } from "@shared/types/Project";

/**
 * Project selector component
 */
export class ProjectSelector {
  constructor(
    private container: HTMLSelectElement,
    private stateManager: StateManager,
    private bridge: VSCodeBridge
  ) {
    // Subscribe to state changes
    this.stateManager.subscribe((state) =>
      this.render(state.projects, state.selectedProjectId)
    );

    // Setup change handler
    this.container.addEventListener("change", async (e) => {
      const target = e.target as HTMLSelectElement;
      await this.bridge.setActiveProject(target.value);
    });
  }

  /**
   * Render project options
   */
  render(projects: Project[], selectedProjectId: string | null) {
    const current = selectedProjectId || "all";
    this.container.innerHTML = '<option value="all">All Projects</option>';

    projects.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.name || p.id;
      this.container.appendChild(opt);
    });

    this.container.value = current;
  }
}
