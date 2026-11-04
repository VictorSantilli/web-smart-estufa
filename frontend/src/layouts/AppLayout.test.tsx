import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';

import { AuthContext } from '@/contexts/authContextValue';
import * as healthService from '@/services/healthService';

import { AppLayout } from './AppLayout';

function renderAs(isAdmin: boolean) {
  vi.spyOn(healthService, 'getHealth').mockResolvedValue({
    status: 'ok',
    database: 'ok',
    version: '0.1.0',
    environment: 'test',
  });
  const user = { id: 1, email: 'x@estufa.com', name: 'X', is_admin: isAdmin };
  render(
    <QueryClientProvider client={new QueryClient()}>
      <AuthContext.Provider value={{ status: 'authenticated', user, login: vi.fn(), logout: vi.fn() }}>
        <MemoryRouter>
          <AppLayout />
        </MemoryRouter>
      </AuthContext.Provider>
    </QueryClientProvider>,
  );
}

describe('AppLayout', () => {
  afterEach(() => vi.restoreAllMocks());

  it('mostra as telas de administração só para ADM', () => {
    renderAs(true);
    expect(screen.getByRole('link', { name: /Usuários/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Estufas e acessos/ })).toBeInTheDocument();
  });

  it('esconde as telas de administração do usuário comum', () => {
    renderAs(false);
    expect(screen.getByRole('link', { name: /Dashboard/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Histórico/ })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Usuários/ })).not.toBeInTheDocument();
  });
});
