import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';

import { AuthContext } from '@/contexts/authContextValue';
import { ToastProvider } from '@/contexts/ToastContext';
import * as greenhouseService from '@/services/greenhouseService';
import * as userService from '@/services/userService';
import type { User } from '@/types/user';

import { UsersPage } from './UsersPage';

const admin = { id: 1, email: 'admin@estufa.com', name: 'Admin', is_admin: true };

function user(overrides: Partial<User>): User {
  return {
    id: 2,
    email: 'ana@estufa.com',
    name: 'Ana',
    is_admin: false,
    is_active: true,
    created_at: '2026-11-01T12:00:00Z',
    greenhouses: [{ id: 1, name: 'Estufa 01' }],
    ...overrides,
  };
}

function renderPage() {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <AuthContext.Provider value={{ status: 'authenticated', user: admin, login: vi.fn(), logout: vi.fn() }}>
        <ToastProvider>
          <MemoryRouter>
            <UsersPage />
          </MemoryRouter>
        </ToastProvider>
      </AuthContext.Provider>
    </QueryClientProvider>,
  );
}

describe('UsersPage', () => {
  beforeEach(() => {
    vi.spyOn(greenhouseService, 'listGreenhouses').mockResolvedValue([{ id: 1, name: 'Estufa 01' }]);
    vi.spyOn(userService, 'listUsers').mockResolvedValue({
      items: [user({ id: 1, email: 'admin@estufa.com', name: 'Admin', is_admin: true }), user({})],
      total: 2,
      page: 1,
      page_size: 20,
    });
  });
  afterEach(() => vi.restoreAllMocks());

  it('lista usuários e não oferece desativar a própria conta', async () => {
    renderPage();
    expect(await screen.findByText('ana@estufa.com')).toBeInTheDocument();
    expect(screen.getByText('Acesso a todas as estufas')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Desativar ana@estufa.com' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Desativar admin@estufa.com' })).not.toBeInTheDocument();
  });

  it('pede confirmação antes de desativar', async () => {
    const setActive = vi.spyOn(userService, 'setUserActive').mockResolvedValue(user({ is_active: false }));
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: 'Desativar ana@estufa.com' }));
    const dialog = screen.getByRole('dialog');
    expect(setActive).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Desativar' }));
    await waitFor(() => expect(setActive).toHaveBeenCalledWith(2, false));
    expect(await screen.findByText('Usuário desativado.')).toBeInTheDocument();
  });

  it('valida o formulário antes de cadastrar', async () => {
    const create = vi.spyOn(userService, 'createUser');
    renderPage();
    await screen.findByText('ana@estufa.com');
    fireEvent.click(screen.getByRole('button', { name: /Novo usuário/ }));
    const dialog = screen.getByRole('dialog');
    fireEvent.change(within(dialog).getByLabelText('Nome'), { target: { value: 'Bruno' } });
    fireEvent.change(within(dialog).getByLabelText('E-mail'), { target: { value: 'bruno@estufa.com' } });
    fireEvent.change(within(dialog).getByLabelText('Senha'), { target: { value: 'curta' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Salvar' }));
    expect(await within(dialog).findByText(/8 a 72 caracteres/)).toBeInTheDocument();
    expect(create).not.toHaveBeenCalled();
  });
});
