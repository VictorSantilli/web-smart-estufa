import { useHealth } from '@/hooks/useHealth';
import { toApiError } from '@/services/api';

import { Spinner } from './ui/Spinner';
import { StatusBadge } from './ui/StatusBadge';

/** Mostra se o frontend está falando com o backend e se o backend alcança o banco. */
export function ApiStatus() {
  const { data, isPending, error } = useHealth();

  if (isPending) return <Spinner label="Verificando servidor..." />;
  if (error) return <StatusBadge tone="critical">{toApiError(error).message}</StatusBadge>;
  if (data.database !== 'ok') return <StatusBadge tone="warning">Banco de dados indisponível</StatusBadge>;
  return <StatusBadge tone="ok">{`Servidor online · v${data.version}`}</StatusBadge>;
}
