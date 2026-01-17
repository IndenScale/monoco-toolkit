/**
 * Project types shared between client, server, and webview
 */

export interface Project {
  id: string;
  name: string;
  path: string;
  description?: string;
}

export interface ProjectMetadata {
  projects: Project[];
  last_active_project_id?: string | null;
}
