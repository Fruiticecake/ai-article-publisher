import axios from 'axios';
import type { PublisherPlatform, ExportFormat } from '../types';

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
      window.location.href = '/dashboard/login';
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Projects
  getProjects: (params?: { limit?: number; offset?: number; keyword?: string; language?: string; min_stars?: number }) =>
    apiClient.get('/projects', { params }).then((res) => res.data),

  getProject: (id: number) =>
    apiClient.get(`/projects/${id}`).then((res) => res.data),

  // Reports
  getReports: (params?: { limit?: number; offset?: number }) =>
    apiClient.get('/reports', { params }).then((res) => res.data),

  getReport: (id: number) =>
    apiClient.get(`/reports/${id}`).then((res) => res.data),

  // Stats
  getStats: () =>
    apiClient.get('/stats').then((res) => res.data),

  // Auth
  login: (username: string, password: string) =>
    apiClient.post('/auth/login', { username, password }).then((res) => res.data),

  logout: () =>
    apiClient.post('/auth/logout').then((res) => res.data),

  // Publishers
  getPublishers: () =>
    apiClient.get('/publishers').then((res) => res.data),

  publishReport: (reportId: number, platforms: PublisherPlatform[]) =>
    apiClient.post(`/publish/${reportId}`, null, { params: { platforms } }).then((res) => res.data),

  // Schedule
  getSchedule: () =>
    apiClient.get('/schedule').then((res) => res.data),

  updateSchedule: (config: { cron: string; timezone: string; platforms?: PublisherPlatform[]; enabled: boolean }) =>
    apiClient.post('/schedule', null, { params: config }).then((res) => res.data),

  triggerNow: (platforms?: PublisherPlatform[]) =>
    apiClient.post('/schedule/trigger', null, { params: { platforms } }).then((res) => res.data),

  // Document Export
  exportDocument: (projectId: number, format: ExportFormat) =>
    apiClient.get('/documents/export', { params: { project_id: projectId, format }, responseType: 'blob' as const }),

  exportMarkdown: (reportId: number) =>
    apiClient.get(`/documents/export/markdown/${reportId}`, { responseType: 'blob' as const }),

  exportPdf: (reportId: number) =>
    apiClient.get(`/documents/export/pdf/${reportId}`, { responseType: 'blob' as const }),

  // Configuration - Publishers
  getPublisherConfig: () =>
    apiClient.get('/config/publishers').then((res) => res.data),

  updatePublisherConfig: (config: Record<string, string>) =>
    apiClient.post('/config/publishers', null, { params: config }).then((res) => res.data),

  // Configuration - LLM
  getLlmConfig: () =>
    apiClient.get('/config/llm').then((res) => res.data),

  updateLlmConfig: (config: { api_key?: string; model?: string; enabled?: boolean }) =>
    apiClient.post('/config/llm', null, { params: config }).then((res) => res.data),

  // Configuration - GitHub
  getGithubConfig: () =>
    apiClient.get('/config/github').then((res) => res.data),

  updateGithubConfig: (config: { token?: string; fetch_count?: number; days_window?: number }) =>
    apiClient.post('/config/github', null, { params: config }).then((res) => res.data),
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
