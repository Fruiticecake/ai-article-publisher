import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

export const useReports = (params?: { limit?: number; offset?: number }) => {
  return useQuery({
    queryKey: ['reports', params],
    queryFn: () => api.getReports(params),
  });
};

export const useReport = (id: number) => {
  return useQuery({
    queryKey: ['report', id],
    queryFn: () => api.getReport(id),
    enabled: !!id,
  });
};
