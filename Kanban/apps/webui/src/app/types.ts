export interface Issue {
  id: string;
  type: string;
  title: string;
  status: string;
  stage?: string;
  parent?: string;
  dependencies?: string[];
  created_at?: string;
  body?: string;
  raw_content?: string;
  tags?: string[];
  path?: string;
  project_id?: string;
}

export interface BoardData {
  draft: Issue[];
  doing: Issue[];
  review: Issue[];
  done: Issue[];
}
