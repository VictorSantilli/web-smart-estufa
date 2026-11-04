import type { Greenhouse, GreenhouseUser } from '@/types/greenhouse';

import { api } from './api';

export async function listGreenhouses(): Promise<Greenhouse[]> {
  const { data } = await api.get<Greenhouse[]>('/greenhouses');
  return data;
}

export async function listGreenhouseUsers(id: number): Promise<GreenhouseUser[]> {
  const { data } = await api.get<GreenhouseUser[]>(`/greenhouses/${id}/users`);
  return data;
}
