import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { AuthContext, type AuthContextValue } from '@/contexts/authContextValue';
import type { CurrentUser } from '@/types/auth';

import { AdminRoute, PrivateRoute } from './guards';

function renderAt(path: string, auth: Partial<AuthContextValue>) {
  const value: AuthContextValue = {
    status: 'anonymous',
    user: null,
    login: vi.fn(),
    logout: vi.fn(),
    ...auth,
  };
  return render(
    <AuthContext.Provider value={value}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/login" element={<p>tela de login</p>} />
          <Route element={<PrivateRoute />}>
            <Route path="/" element={<p>dashboard</p>} />
            <Route element={<AdminRoute />}>
              <Route path="/usuarios" element={<p>usuarios</p>} />
            </Route>
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

const common: CurrentUser = { id: 2, email: 'ana@estufa.com', name: 'Ana', is_admin: false };
const admin: CurrentUser = { ...common, id: 1, is_admin: true };

describe('guards', () => {
  it('redireciona visitante para o login', () => {
    renderAt('/', { status: 'anonymous' });
    expect(screen.getByText('tela de login')).toBeInTheDocument();
  });

  it('mostra carregamento enquanto a sessão é recuperada', () => {
    renderAt('/', { status: 'loading' });
    expect(screen.getByText('Carregando sessão...')).toBeInTheDocument();
  });

  it('libera rota privada para usuário autenticado', () => {
    renderAt('/', { status: 'authenticated', user: common });
    expect(screen.getByText('dashboard')).toBeInTheDocument();
  });

  it('bloqueia área de ADM para usuário comum', () => {
    renderAt('/usuarios', { status: 'authenticated', user: common });
    expect(screen.getByText('Acesso restrito')).toBeInTheDocument();
    expect(screen.queryByText('usuarios')).not.toBeInTheDocument();
  });

  it('libera área de ADM para administrador', () => {
    renderAt('/usuarios', { status: 'authenticated', user: admin });
    expect(screen.getByText('usuarios')).toBeInTheDocument();
  });
});
