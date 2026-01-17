/**
 * Workspace Indexer Service
 * Manages the index of issues and projects in the workspace
 */

import * as path from "path";
import { CLIExecutor } from "./CLIExecutor";

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

export interface Project {
  id: string;
  name: string;
  path: string;
}

export class WorkspaceIndexer {
  private issueCache: Map<string, IssueIndex> = new Map();
  private projectCache: Project[] = [];
  private isScanning = false;
  private logger?: (message: string) => void;

  constructor(
    private workspaceRoot: string,
    private cliExecutor: CLIExecutor,
    logger?: (message: string) => void,
  ) {
    this.logger = logger;
  }

  /**
   * Scan the workspace for projects and issues
   */
  async scan(): Promise<void> {
    if (this.isScanning) {
      return;
    }
    this.isScanning = true;

    this.log(`Scanning workspace: ${this.workspaceRoot}`);

    try {
      // 1. Scan Projects first
      await this.scanProjects();

      // 2. Scan Issues
      await this.scanIssues();
    } finally {
      this.isScanning = false;
    }
  }

  /**
   * Scan projects
   */
  private async scanProjects(): Promise<void> {
    try {
      const stdout = await this.cliExecutor.execute(
        ["project", "list", "--json"],
        this.workspaceRoot,
      );
      this.projectCache = JSON.parse(stdout);
    } catch (e: any) {
      this.logError(`Project scan failed: ${e.message}`);
    }
  }

  /**
   * Scan issues
   */
  private async scanIssues(): Promise<void> {
    try {
      const stdout = await this.cliExecutor.execute(
        ["issue", "list", "--status", "all", "--json", "--workspace"],
        this.workspaceRoot,
      );

      if (stdout.trim()) {
        const issues = JSON.parse(stdout);
        this.issueCache.clear();

        issues.forEach((raw: any) => {
          // Security Boundary: Ensure issue is within the current workspace
          const relativePath = path.relative(this.workspaceRoot, raw.path);
          if (relativePath.startsWith("..") || path.isAbsolute(relativePath)) {
            return;
          }

          // Determine project_id based on path mapping
          let projectId = "default";
          if (this.projectCache.length > 0) {
            // Find which project path the issue file is under
            const match = [...this.projectCache]
              .sort((a, b) => (b.path?.length || 0) - (a.path?.length || 0))
              .find((p: any) => {
                const issuePath = raw.path?.toLowerCase();
                const projectPath = p.path?.toLowerCase();
                return (
                  issuePath && projectPath && issuePath.startsWith(projectPath)
                );
              });
            if (match) {
              projectId = match.id;
            } else {
              projectId = this.projectCache[0].id;
            }
          }

          // Map raw to IssueIndex
          this.issueCache.set(raw.id, {
            ...raw,
            project_id: projectId,
            filePath: raw.path,
            uri: `file://${raw.path}`,
          });
        });

        this.log(`Synced ${this.issueCache.size} issues from CLI.`);
      }
    } catch (e: any) {
      this.logError(`Issue scan failed: ${e.message}`);
    }
  }

  /**
   * Get an issue by ID
   */
  getIssue(id: string): IssueIndex | undefined {
    return this.issueCache.get(id);
  }

  /**
   * Get all issues
   */
  getAllIssues(): IssueIndex[] {
    return Array.from(this.issueCache.values());
  }

  /**
   * Get all projects
   */
  getProjects(): Project[] {
    return this.projectCache;
  }

  /**
   * Log a message
   */
  private log(message: string) {
    if (this.logger) {
      this.logger(`[Monoco LSP] ${message}`);
    }
  }

  /**
   * Log an error
   */
  private logError(message: string) {
    if (this.logger) {
      this.logger(`[Monoco LSP] ERROR: ${message}`);
    }
  }
}
