import type { ReactNode } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { Spinner } from '@/components/ui/Spinner';
import { useAuth } from '@/hooks/useAuth';
import { ForbiddenPage } from '@/pages/ForbiddenPage';

import { paths } from './paths';

function FullPageLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Spinner label="Carregando sessão..." />
    </div>
  );
}

/** Exige sessão. Quem não está logado vai para o login e volta depois para onde estava. */
export function PrivateRoute() {
  const { status } = useAuth();
  const location = useLocation();
  if (status === 'loading') return <FullPageLoading />;
  if (status === 'anonymous') {
    return <Navigate to={paths.login} replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}

/** Exige perfil ADM. É só conveniência de interface: o backend valida de novo. */
export function AdminRoute({ children }: { children?: ReactNode }) {
  const { user } = useAuth();
  if (!user?.is_admin) return <ForbiddenPage />;
  return children ?? <Outlet />;
}

/** Tela de login: quem já está logado vai direto ao Dashboard. */
export function PublicOnlyRoute() {
  const { status } = useAuth();
  if (status === 'loading') return <FullPageLoading />;
  if (status === 'authenticated') return <Navigate to={paths.dashboard} replace />;
  return <Outlet />;
}
