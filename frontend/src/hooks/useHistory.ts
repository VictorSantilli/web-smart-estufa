import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { getHistory } from '@/services/historyService';
import type { HistoryQuery } from '@/types/history';

export function useHistory(greenhouseId: number | null, query: HistoryQuery | null) {
  return useQuery({
    queryKey: ['history', greenhouseId, query],
    queryFn: () => getHistory(greenhouseId!, query!),
    enabled: greenhouseId !== null && query !== null,
    placeholderData: keepPreviousData,
    // 24 h muda a cada medição; os agregados diários mudam pouco.
    refetchInterval: query && 'period' in query && query.period === '24h' ? 60_000 : false,
    staleTime: 30_000,
  });
}
