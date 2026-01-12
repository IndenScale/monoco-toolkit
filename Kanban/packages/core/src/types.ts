export interface Issue {
  id: string;
  type: string;
  title: string;
  status: string;
  stage?: string;
  created_at: string;
  parent?: string;
  dependencies?: string[];
  related?: string[];
  solution?: string;
}

export interface Project {
  id: string;
  name: string;
  path: string;
  issues_path: string;
}

export interface DaemonInfo {
  name: string;
  id?: string;
  version: string;
  mode: string;
  head?: string;
}

export interface DaemonEvent {
  event: string;
  data: any;
}

export type DaemonStatus =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error";

export type ActivityType = "created" | "updated" | "closed";

export interface ActivityItem {
  id: string;
  type: ActivityType;
  issue_id: string;
  issue_title: string;
  timestamp: string;
  description?: string;
}

export interface DashboardStats {
  total_backlog: number;
  completed_this_week: number;
  blocked_issues_count: number;
  velocity_trend: number;
  recent_activities: ActivityItem[];
}
