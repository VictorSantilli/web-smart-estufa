import type { DashboardData } from '@/types/dashboard';

import { api } from './api';

export async function getDashboard(greenhouseId: number): Promise<DashboardData> {
  const { data } = await api.get<DashboardData>(`/dashboard/${greenhouseId}`);
  return data;
}
