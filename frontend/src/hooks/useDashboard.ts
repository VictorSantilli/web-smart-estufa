import { useQuery } from '@tanstack/react-query';

import { getDashboard } from '@/services/dashboardService';

export const DASHBOARD_REFRESH_MS = 60_000;

export function useDashboard(greenhouseId: number | null) {
  return useQuery({
    queryKey: ['dashboard', greenhouseId],
    queryFn: () => getDashboard(greenhouseId!),
    enabled: greenhouseId !== null,
    refetchInterval: DASHBOARD_REFRESH_MS,
    refetchIntervalInBackground: false,
  });
}
