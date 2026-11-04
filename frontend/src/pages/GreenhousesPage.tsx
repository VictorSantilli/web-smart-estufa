import { Link } from 'react-router-dom';

import { ShieldCheck, Sprout, Users } from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Spinner } from '@/components/ui/Spinner';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useGreenhouses, useGreenhouseUsers } from '@/hooks/useGreenhouses';
import { toApiError } from '@/services/api';
import { paths } from '@/routes/paths';
import type { Greenhouse } from '@/types/greenhouse';
import { formatDateOnly } from '@/utils/datetime';

function GreenhouseCard({ greenhouse }: { greenhouse: Greenhouse }) {
  const users = useGreenhouseUsers(greenhouse.id);
  return (
    <Card title={greenhouse.name ?? `Estufa ${greenhouse.id}`} icon={<Sprout className="h-4 w-4 text-brand-600" />}>
      {users.isPending ? (
        <Spinner />
      ) : users.isError ? (
        <p className="text-sm text-red-600">{toApiError(users.error).message}</p>
      ) : users.data.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum usuário comum vinculado.</p>
      ) : (
        <ul className="divide-y divide-gray-100">
          {users.data.map((u) => (
            <li key={u.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-gray-800">{u.name ?? u.email}</p>
                <p className="truncate text-xs text-gray-500">
                  {u.email} · desde {formatDateOnly(u.linked_at)}
                </p>
              </div>
              {!u.is_active && <StatusBadge tone="neutral">Desativado</StatusBadge>}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export function GreenhousesPage() {
  const greenhouses = useGreenhouses();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Estufas e acessos</h1>
        <p className="text-sm text-gray-500">
          Usuários com permissão em cada estufa. Para conceder ou remover acesso, edite o usuário em{' '}
          <Link to={paths.users} className="font-medium text-brand-700 hover:underline">
            Usuários
          </Link>
          .
        </p>
      </div>
      <div className="flex items-center gap-2 rounded-lg bg-brand-50 px-4 py-3 text-sm text-brand-800">
        <ShieldCheck className="h-4 w-4 shrink-0" aria-hidden />
        Administradores têm acesso a todas as estufas e não aparecem nas listas abaixo.
      </div>

      {greenhouses.isPending ? (
        <Spinner />
      ) : greenhouses.isError ? (
        <ErrorState message={toApiError(greenhouses.error).message} onRetry={() => greenhouses.refetch()} />
      ) : greenhouses.data.length === 0 ? (
        <EmptyState icon={<Users className="h-10 w-10" aria-hidden />} title="Nenhuma estufa cadastrada" />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {greenhouses.data.map((g) => (
            <GreenhouseCard key={g.id} greenhouse={g} />
          ))}
        </div>
      )}
    </div>
  );
}
