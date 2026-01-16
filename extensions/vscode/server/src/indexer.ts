import * as fs from "fs";
import * as path from "path";
import * as yaml from "js-yaml";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

export interface IssueIndex {
  id: string;
  type: string;
  title: string;
  status: string;
  stage: string;
  parent?: string;
  solution?: string;
  dependencies?: string[];
  related?: string[];
  tags?: string[];
  project_id: string;
  filePath: string;
  uri: string;
}

export interface WorkspaceMetadata {
  last_active_project_id: string | null;
  projects: { id: string; name: string }[];
}

export class WorkspaceIndexer {
  private index: Map<string, IssueIndex> = new Map();
  private workspaceRoot: string | null = null;
  private discoveredProjects: Set<string> = new Set();

  setWorkspaceRoot(root: string) {
    this.workspaceRoot = root;
  }

  async scan(executable: string = "monoco") {
    if (!this.workspaceRoot) return;
    this.index.clear();
    this.discoveredProjects.clear();

    try {
      // Use monoco CLI to discover projects
      const { stdout } = await execAsync(`${executable} project list --json --root "${this.workspaceRoot}"`, { 
        encoding: 'utf-8',
        timeout: 10000 // 10s timeout
      });
      const projects = JSON.parse(stdout);
      
      for (const p of projects) {
        // p: { id, name, path, key }
        this.discoveredProjects.add(p.id);
        this.scanProjectDir(p.path, p.id);
      }
    } catch (e) {
      console.error("Failed to discover projects via CLI:", e);
      // If CLI fails, we might be in an environment without monoco installed.
      // But per instructions, we rely on CLI.
    }
  }

  private scanProjectDir(projectPath: string, defaultProjectId: string) {
    const issuesDir = path.join(projectPath, "Issues");
    if (fs.existsSync(issuesDir)) {
      this.scanDir(issuesDir, defaultProjectId);
    }
  }

  private scanDir(dir: string, currentProjectId?: string) {
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          if (entry.name.startsWith(".") || entry.name === "node_modules")
            continue;
          this.scanDir(fullPath, currentProjectId);
        } else if (entry.isFile() && entry.name.endsWith(".md")) {
          this.indexFile(fullPath, currentProjectId);
        }
      }
    } catch (e) {
      // ignore
    }
  }

  public indexFile(filePath: string, defaultProjectId?: string) {
    try {
      const content = fs.readFileSync(filePath, "utf-8");
      const frontmatterRegex = /^---\n([\s\S]*?)\n---/;
      const match = frontmatterRegex.exec(content);
      if (match) {
        const data = yaml.load(match[1]) as any;
        if (data && data.id) {
          // If project_id is missing in frontmatter, try to infer it
          let projectId = data.project_id || defaultProjectId;

          // If still missing, try to infer from path: workspace/ProjectName/Issues/...
          if (!projectId && this.workspaceRoot) {
            const relative = path.relative(this.workspaceRoot, filePath);
            const parts = relative.split(path.sep);
            if (parts.length > 1 && parts[1] === "Issues") {
              projectId = parts[0];
            }
          }

          this.index.set(data.id, {
            id: data.id,
            type: data.type,
            title: data.title,
            status: data.status,
            stage: data.stage,
            parent: data.parent,
            solution: data.solution,
            dependencies: data.dependencies,
            related: data.related,
            tags: data.tags,
            project_id: projectId || "Default",
            filePath: filePath,
            uri: `file://${filePath}`,
          });
        }
      }
    } catch (e) {
      // ignore
    }
  }

  public getMetadata(): WorkspaceMetadata {
    const metadata: WorkspaceMetadata = {
      last_active_project_id: null,
      projects: [],
    };

    if (!this.workspaceRoot) return metadata;

    // 1. Load state.json
    const statePath = path.join(this.workspaceRoot, ".monoco", "state.json");
    if (fs.existsSync(statePath)) {
      try {
        const state = JSON.parse(fs.readFileSync(statePath, "utf-8"));
        metadata.last_active_project_id = state.last_active_project_id || null;
      } catch (e) {}
    }

    // 2. Extract projects from index and discovered list
    const projectSet = new Set<string>(this.discoveredProjects);
    for (const issue of this.index.values()) {
      projectSet.add(issue.project_id);
    }
    metadata.projects = Array.from(projectSet).map((id) => ({ id, name: id }));

    return metadata;
  }

  get(id: string) {
    return this.index.get(id);
  }

  getAll() {
    return Array.from(this.index.values());
  }
}
