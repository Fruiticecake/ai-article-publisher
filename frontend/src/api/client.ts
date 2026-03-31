import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
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
  }
);

export const api = {
  // Projects
  getProjects: (params?: { limit?: number; offset?: number }) =>
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
};
