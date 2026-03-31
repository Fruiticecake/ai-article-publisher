import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

export const useProjects = (params?: { limit?: number; offset?: number }) => {
  return useQuery({
    queryKey: ['projects', params],
    queryFn: () => api.getProjects(params),
  });
};

export const useProject = (id: number) => {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => api.getProject(id),
    enabled: !!id,
  });
};
