export interface Project {
  id: number;
  source: string;
  source_id: string;
  full_name: string;
  html_url: string;
  description: string;
  stars: number;
  forks: number;
  language: string;
  topics: string[];
  readme?: string;
  rank: number;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, any>;
}

export interface Report {
  id: number;
  title: string;
  project_id?: number;
  content_markdown?: string;
  generated_at?: string;
  published_at?: Record<string, string>;
  insights?: string[];
  quality_score: number;
}

export interface Stats {
  total_projects: number;
  total_reports: number;
}
