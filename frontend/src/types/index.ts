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

// 发布平台相关类型
export type PublisherPlatform = 'notion' | 'csdn' | 'zhihu' | 'juejin' | 'telegram' | 'xhs';

export interface PublisherInfo {
  name: string;
  type: PublisherPlatform;
  enabled: boolean;
  description: string;
}

export interface PublishResult {
  success: boolean;
  result: string;
  timestamp: string;
}

export interface PublishResponse {
  success: boolean;
  report_id: number;
  platforms: Record<PublisherPlatform, PublishResult>;
}

// 定时任务相关类型
export interface ScheduleConfig {
  enabled: boolean;
  cron: string;
  timezone: string;
  platforms: PublisherPlatform[];
}

export interface ScheduleResponse {
  success: boolean;
  config: ScheduleConfig;
}

export interface TriggerResponse {
  success: boolean;
  message: string;
  platforms: PublisherPlatform[];
  timestamp: string;
}

// 文档导出相关类型
export type ExportFormat = 'pdf' | 'markdown';

export interface ExportRequest {
  project_id: number;
  format: ExportFormat;
}

// 配置相关类型
export interface PublisherConfig {
  notion_token: string;
  notion_database_id: string;
  csdn_api: string;
  csdn_token: string;
  zhihu_token: string;
  juejin_token: string;
  telegram_bot_token: string;
  telegram_chat_id: string;
  xhs_cookie: string;
}

export interface LlmConfig {
  api_key: string;
  model: string;
  enabled: boolean;
}

export interface GithubConfig {
  token: string;
  fetch_count: number;
  days_window: number;
}

export interface ConfigSaveResponse {
  success: boolean;
  message: string;
}
