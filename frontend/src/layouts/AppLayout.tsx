import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';

import { History, LayoutDashboard, Leaf, Menu, Sprout, UserCircle2, Users, X } from 'lucide-react';

import { ApiStatus } from '@/components/ApiStatus';
import { paths } from '@/routes/paths';
import { cn } from '@/utils/cn';

const navItems = [
  { to: paths.dashboard, label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: paths.history, label: 'Histórico', icon: History },
  // Itens de ADM: visíveis apenas para administradores a partir da Etapa 3
  { to: paths.users, label: 'Usuários', icon: Users },
  { to: paths.greenhouses, label: 'Estufas e acessos', icon: Sprout },
];

export function AppLayout() {
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen lg:flex">
      {/* Fundo escuro do menu no celular */}
      {open && (
        <div className="fixed inset-0 z-30 bg-gray-900/40 lg:hidden" onClick={() => setOpen(false)} aria-hidden />
      )}

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-brand-900 text-brand-50 transition-transform lg:static lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex h-16 items-center justify-between px-5">
          <span className="flex items-center gap-2 text-lg font-semibold">
            <Leaf className="h-6 w-6 text-brand-300" aria-hidden />
            Smart Estufa
          </span>
          <button className="lg:hidden" onClick={() => setOpen(false)} aria-label="Fechar menu">
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive ? 'bg-brand-700 text-white' : 'text-brand-100 hover:bg-brand-800',
                )
              }
            >
              <Icon className="h-5 w-5" aria-hidden />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-4 border-b border-gray-200 bg-white px-4 sm:px-6">
          <button className="text-gray-600 lg:hidden" onClick={() => setOpen(true)} aria-label="Abrir menu">
            <Menu className="h-6 w-6" />
          </button>
          <div className="hidden sm:block">
            <ApiStatus />
          </div>
          {/* Dados do usuário autenticado: Etapa 3 */}
          <div className="ml-auto flex items-center gap-2 text-sm text-gray-600">
            <UserCircle2 className="h-7 w-7 text-gray-400" aria-hidden />
            <span className="hidden sm:inline">Visitante</span>
          </div>
        </header>
        <main className="flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
