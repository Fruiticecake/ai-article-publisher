'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

export const useStats = () => {
  return useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getStats(),
  });
};
