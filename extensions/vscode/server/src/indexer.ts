import * as fs from "fs";
import * as path from "path";
import * as yaml from "js-yaml";

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
  project_id?: string;
  filePath: string;
  uri: string;
}

export class WorkspaceIndexer {
  private index: Map<string, IssueIndex> = new Map();
  private workspaceRoot: string | null = null;

  setWorkspaceRoot(root: string) {
    this.workspaceRoot = root;
  }

  scan() {
    if (!this.workspaceRoot) return;
    this.index.clear();
    const issuesDir = path.join(this.workspaceRoot, "Issues");
    if (fs.existsSync(issuesDir)) {
      this.scanDir(issuesDir);
    } else {
      // Fallback to scanning root if Issues folders are scattered or named differently,
      // but Monoco spec says Issues/
      this.scanDir(this.workspaceRoot);
    }
  }

  private scanDir(dir: string) {
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          if (entry.name.startsWith(".") || entry.name === "node_modules")
            continue;
          this.scanDir(fullPath);
        } else if (entry.isFile() && entry.name.endsWith(".md")) {
          this.indexFile(fullPath);
        }
      }
    } catch (e) {
      console.error(`Failed to scan directory ${dir}:`, e);
    }
  }

  public indexFile(filePath: string) {
    try {
      const content = fs.readFileSync(filePath, "utf-8");
      const frontmatterRegex = /^---\n([\s\S]*?)\n---/;
      const match = frontmatterRegex.exec(content);
      if (match) {
        const data = yaml.load(match[1]) as any;
        if (data && data.id) {
          // Normalize ID to be the key
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
            project_id: data.project_id,
            filePath: filePath,
            uri: `file://${filePath}`,
          });
        }
      }
    } catch (e) {
      // console.error(`Failed to index ${filePath}:`, e);
    }
  }

  get(id: string) {
    return this.index.get(id);
  }

  getAll() {
    return Array.from(this.index.values());
  }
}
