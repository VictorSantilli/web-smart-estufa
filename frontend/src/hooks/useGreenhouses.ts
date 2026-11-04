import { useQuery } from '@tanstack/react-query';

import { listGreenhouses, listGreenhouseUsers } from '@/services/greenhouseService';

export function useGreenhouses() {
  return useQuery({ queryKey: ['greenhouses'], queryFn: listGreenhouses });
}

export function useGreenhouseUsers(id: number) {
  return useQuery({ queryKey: ['greenhouses', id, 'users'], queryFn: () => listGreenhouseUsers(id) });
}
