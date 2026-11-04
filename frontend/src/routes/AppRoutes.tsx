import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';

import { AppLayout } from '@/layouts/AppLayout';
import { DashboardPage } from '@/pages/DashboardPage';
import { DetectionsPage } from '@/pages/DetectionsPage';
import { GreenhousesPage } from '@/pages/GreenhousesPage';
import { LoginPage } from '@/pages/LoginPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { UsersPage } from '@/pages/UsersPage';
import { Spinner } from '@/components/ui/Spinner';

import { AdminRoute, PrivateRoute, PublicOnlyRoute } from './guards';
import { paths } from './paths';

// Os gráficos (Recharts) só são baixados quando o usuário abre o Histórico.
const HistoryPage = lazy(() => import('@/pages/HistoryPage').then((m) => ({ default: m.HistoryPage })));

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route path={paths.login} element={<LoginPage />} />
      </Route>

      <Route element={<PrivateRoute />}>
        <Route element={<AppLayout />}>
          <Route path={paths.dashboard} element={<DashboardPage />} />
          <Route path={paths.history} element={
              <Suspense fallback={<Spinner />}>
                <HistoryPage />
              </Suspense>
            } />
          <Route path={paths.detections} element={<DetectionsPage />} />
          <Route element={<AdminRoute />}>
            <Route path={paths.users} element={<UsersPage />} />
            <Route path={paths.greenhouses} element={<GreenhousesPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
