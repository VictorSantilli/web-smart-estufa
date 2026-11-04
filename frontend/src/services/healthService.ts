import type { HealthResponse } from '@/types/api';

import { api } from './api';

export async function getHealth(): Promise<HealthResponse> {
  // 503 também traz o corpo com o status do banco, então não é tratado como exceção.
  const { data } = await api.get<HealthResponse>('/health', {
    validateStatus: (status) => status === 200 || status === 503,
  });
  return data;
}
