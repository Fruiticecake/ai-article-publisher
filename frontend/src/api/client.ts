import axios from 'axios';
import type {
  Project,
  Report,
  StatsResponse,
  ProjectStats,
  AuthResponse,
  User,
  PublisherInfo,
  PublishResponse,
  ScheduleConfig,
  TriggerResponse,
  PublisherConfig,
  LlmConfig,
  GithubConfig,
  ConfigSaveResponse,
  PublisherPlatform,
  ExportFormat,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);

export const api = {
  // Projects
  getProjects: (params?: { limit?: number; offset?: number; keyword?: string; language?: string; min_stars?: number }): Promise<Project[]> =>
    apiClient.get('/projects', { params }).then((res) => res.data),

  getProject: (id: number): Promise<Project> =>
    apiClient.get(`/projects/${id}`).then((res) => res.data),

  // Reports
  getReports: (params?: { limit?: number; offset?: number }): Promise<Report[]> =>
    apiClient.get('/reports', { params }).then((res) => res.data),

  getReport: (id: number): Promise<Report> =>
    apiClient.get(`/reports/${id}`).then((res) => res.data),

  // Stats
  getStats: (): Promise<StatsResponse> =>
    apiClient.get('/stats').then((res) => res.data),

  getProjectStats: (): Promise<ProjectStats> =>
    apiClient.get('/stats/project').then((res) => res.data),

  // Auth
  login: (username: string, password: string): Promise<AuthResponse> =>
    apiClient.post('/auth/login', { username, password }).then((res) => res.data),

  logout: (): Promise<{ success: boolean }> =>
    apiClient.post('/auth/logout').then((res) => res.data),

  getMe: (): Promise<{ success: boolean; user: User }> =>
    apiClient.get('/auth/me').then((res) => res.data),

  // Publishers
  getPublishers: (): Promise<PublisherInfo[]> =>
    apiClient.get('/publishers').then((res) => res.data),

  publishReport: (reportId: number, platforms: PublisherPlatform[]): Promise<PublishResponse> =>
    apiClient.post(`/publish/${reportId}`, null, { params: { platforms } }).then((res) => res.data),

  // Schedule
  getSchedule: (): Promise<ScheduleConfig & { enabled_publishers: PublisherPlatform[] }> =>
    apiClient.get('/schedule').then((res) => res.data),

  updateSchedule: (config: { cron: string; timezone: string; platforms?: PublisherPlatform[]; enabled: boolean }): Promise<ConfigSaveResponse> =>
    apiClient.post('/schedule', null, { params: config }).then((res) => res.data),

  triggerNow: (platforms?: PublisherPlatform[]): Promise<TriggerResponse> =>
    apiClient.post('/schedule/trigger', null, { params: { platforms } }).then((res) => res.data),

  publishAllUnpublished: (platforms?: PublisherPlatform[]): Promise<TriggerResponse> =>
    apiClient.post('/publish/unpublished', null, { params: { platforms } }).then((res) => res.data),

  // Document Export
  exportDocument: (projectId: number, format: ExportFormat) =>
    apiClient.get('/documents/export', { params: { project_id: projectId, format }, responseType: 'blob' as const }),

  exportMarkdown: (reportId: number) =>
    apiClient.get(`/documents/export/markdown/${reportId}`, { responseType: 'blob' as const }),

  exportPdf: (reportId: number) =>
    apiClient.get(`/documents/export/pdf/${reportId}`, { responseType: 'blob' as const }),

  // Configuration - Publishers
  getPublisherConfig: (): Promise<PublisherConfig> =>
    apiClient.get('/config/publishers').then((res) => res.data),

  updatePublisherConfig: (config: Partial<PublisherConfig>): Promise<ConfigSaveResponse> =>
    apiClient.post('/config/publishers', null, { params: config }).then((res) => res.data),

  // Configuration - LLM
  getLlmConfig: (): Promise<LlmConfig> =>
    apiClient.get('/config/llm').then((res) => res.data),

  updateLlmConfig: (config: Partial<LlmConfig>): Promise<ConfigSaveResponse> =>
    apiClient.post('/config/llm', null, { params: config }).then((res) => res.data),

  // Configuration - GitHub
  getGithubConfig: (): Promise<GithubConfig> =>
    apiClient.get('/config/github').then((res) => res.data),

  updateGithubConfig: (config: Partial<GithubConfig>): Promise<ConfigSaveResponse> =>
    apiClient.post('/config/github', null, { params: config }).then((res) => res.data),

  // Health check
  healthCheck: (): Promise<{ status: string; version: string; timestamp: string }> =>
    apiClient.get('/health').then((res) => res.data),
};

// 导出工具函数
export const downloadBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};
