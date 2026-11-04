import { useEffect, useState } from 'react';

import { Pencil, Plus, Power, Search, ShieldCheck } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Modal } from '@/components/ui/Modal';
import { Spinner } from '@/components/ui/Spinner';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { UserFormModal } from '@/components/users/UserFormModal';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/useToast';
import { useToggleUserActive, useUsers } from '@/hooks/useUsers';
import { toApiError } from '@/services/api';
import type { User } from '@/types/user';

const PAGE_SIZE = 10;
type ActiveFilter = 'all' | 'active' | 'inactive';

export function UsersPage() {
  const { user: me } = useAuth();
  const toast = useToast();
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<ActiveFilter>('all');
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<User | null | undefined>(undefined); // undefined = fechado
  const [confirming, setConfirming] = useState<User | null>(null);
  const toggleActive = useToggleUserActive();

  // Busca com pequeno atraso para não consultar a API a cada tecla
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const query = useUsers({
    q: search || undefined,
    active: filter === 'all' ? undefined : filter === 'active',
    page,
    page_size: PAGE_SIZE,
  });
  const totalPages = query.data ? Math.max(1, Math.ceil(query.data.total / PAGE_SIZE)) : 1;

  async function confirmToggle() {
    if (!confirming) return;
    try {
      await toggleActive.mutateAsync({ id: confirming.id, active: !confirming.is_active });
      toast.success(confirming.is_active ? 'Usuário desativado.' : 'Usuário reativado.');
    } catch (error) {
      toast.error(toApiError(error).message);
    } finally {
      setConfirming(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Usuários</h1>
          <p className="text-sm text-gray-500">Cadastro, perfis e acesso às estufas.</p>
        </div>
        <Button onClick={() => setEditing(null)}>
          <Plus className="h-4 w-4" aria-hidden />
          Novo usuário
        </Button>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" aria-hidden />
          <input
            type="search"
            aria-label="Buscar por nome ou e-mail"
            placeholder="Buscar por nome ou e-mail"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full rounded-lg border border-gray-300 py-2 pl-9 pr-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
          />
        </div>
        <select
          aria-label="Filtrar por situação"
          value={filter}
          onChange={(e) => {
            setFilter(e.target.value as ActiveFilter);
            setPage(1);
          }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
        >
          <option value="all">Todos</option>
          <option value="active">Ativos</option>
          <option value="inactive">Desativados</option>
        </select>
      </div>

      {query.isPending ? (
        <Spinner />
      ) : query.isError ? (
        <ErrorState message={toApiError(query.error).message} onRetry={() => query.refetch()} />
      ) : query.data.items.length === 0 ? (
        <EmptyState title="Nenhum usuário encontrado" description="Ajuste a busca ou cadastre um novo usuário." />
      ) : (
        <>
          <ul className="divide-y divide-gray-100 overflow-hidden rounded-xl border border-gray-200 bg-white">
            {query.data.items.map((u) => (
              <li key={u.id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="truncate font-medium text-gray-900">{u.name ?? u.email}</p>
                    {u.is_admin && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
                        <ShieldCheck className="h-3 w-3" aria-hidden /> ADM
                      </span>
                    )}
                    <StatusBadge tone={u.is_active ? 'ok' : 'neutral'}>{u.is_active ? 'Ativo' : 'Desativado'}</StatusBadge>
                  </div>
                  <p className="truncate text-sm text-gray-500">{u.email}</p>
                  <p className="mt-1 text-xs text-gray-500">
                    {u.is_admin
                      ? 'Acesso a todas as estufas'
                      : u.greenhouses.length
                        ? u.greenhouses.map((g) => g.name ?? `Estufa ${g.id}`).join(', ')
                        : 'Sem acesso a estufas'}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={() => setEditing(u)} aria-label={`Editar ${u.email}`}>
                    <Pencil className="h-4 w-4" aria-hidden />
                    Editar
                  </Button>
                  {u.id !== me?.id && (
                    <Button
                      variant={u.is_active ? 'ghost' : 'secondary'}
                      onClick={() => setConfirming(u)}
                      aria-label={`${u.is_active ? 'Desativar' : 'Reativar'} ${u.email}`}
                    >
                      <Power className="h-4 w-4" aria-hidden />
                      {u.is_active ? 'Desativar' : 'Reativar'}
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>

          <nav className="flex items-center justify-between text-sm text-gray-600" aria-label="Paginação">
            <span>
              {query.data.total} usuário(s) · página {page} de {totalPages}
            </span>
            <div className="flex gap-2">
              <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Anterior
              </Button>
              <Button variant="secondary" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                Próxima
              </Button>
            </div>
          </nav>
        </>
      )}

      {editing !== undefined && me && (
        <UserFormModal
          key={editing?.id ?? 'new'}
          open
          user={editing}
          currentUserId={me.id}
          onClose={() => setEditing(undefined)}
        />
      )}

      <Modal
        open={confirming !== null}
        onClose={() => setConfirming(null)}
        title={confirming?.is_active ? 'Desativar usuário' : 'Reativar usuário'}
        footer={
          <>
            <Button variant="secondary" onClick={() => setConfirming(null)}>
              Cancelar
            </Button>
            <Button variant={confirming?.is_active ? 'danger' : 'primary'} loading={toggleActive.isPending} onClick={confirmToggle}>
              {confirming?.is_active ? 'Desativar' : 'Reativar'}
            </Button>
          </>
        }
      >
        <p className="text-sm text-gray-600">
          {confirming?.is_active
            ? `${confirming.email} perderá o acesso imediatamente e as sessões abertas serão encerradas.`
            : `${confirming?.email} poderá entrar novamente no sistema.`}
        </p>
      </Modal>
    </div>
  );
}
