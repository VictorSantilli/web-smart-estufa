import type { HistoryData, HistoryQuery } from '@/types/history';

import { api } from './api';

export async function getHistory(greenhouseId: number, query: HistoryQuery): Promise<HistoryData> {
  const { data } = await api.get<HistoryData>(`/history/${greenhouseId}`, { params: query });
  return data;
}
