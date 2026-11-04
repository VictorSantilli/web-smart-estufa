import { Route, Routes } from 'react-router-dom';

import { AppLayout } from '@/layouts/AppLayout';
import { AdminPlaceholderPage } from '@/pages/AdminPlaceholderPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { HistoryPage } from '@/pages/HistoryPage';
import { NotFoundPage } from '@/pages/NotFoundPage';

import { paths } from './paths';

/**
 * Na Etapa 3 entram /login (pública) e os guards: PrivateRoute (exige sessão)
 * e AdminRoute (exige perfil ADM). A autorização real continua no backend.
 */
export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path={paths.dashboard} element={<DashboardPage />} />
        <Route path={paths.history} element={<HistoryPage />} />
        <Route path={paths.users} element={<AdminPlaceholderPage title="Usuários" />} />
        <Route path={paths.greenhouses} element={<AdminPlaceholderPage title="Estufas e acessos" />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
