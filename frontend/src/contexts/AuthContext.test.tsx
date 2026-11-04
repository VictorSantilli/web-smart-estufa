import { act, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { useAuth } from '@/hooks/useAuth';
import * as api from '@/services/api';
import * as authService from '@/services/authService';

import { AuthProvider } from './AuthContext';

function Probe() {
  const { status, user, logout } = useAuth();
  return (
    <div>
      <p>status: {status}</p>
      <p>user: {user?.email ?? '-'}</p>
      <button onClick={() => void logout()}>sair</button>
    </div>
  );
}

function renderWithAuth(client = new QueryClient()) {
  render(
    <QueryClientProvider client={client}>
      <AuthProvider>
        <Probe />
      </AuthProvider>
    </QueryClientProvider>,
  );
  return client;
}

const me = { id: 1, email: 'ana@estufa.com', name: 'Ana', is_admin: false };

describe('AuthProvider', () => {
  afterEach(() => vi.restoreAllMocks());

  it('recupera a sessão pelo cookie de refresh ao abrir a página', async () => {
    vi.spyOn(api, 'refreshAccessToken').mockResolvedValue('token');
    vi.spyOn(authService, 'getMe').mockResolvedValue(me);
    renderWithAuth();
    expect(await screen.findByText('status: authenticated')).toBeInTheDocument();
    expect(screen.getByText('user: ana@estufa.com')).toBeInTheDocument();
  });

  it('fica anônimo quando não há sessão', async () => {
    vi.spyOn(api, 'refreshAccessToken').mockRejectedValue(new Error('401'));
    renderWithAuth();
    expect(await screen.findByText('status: anonymous')).toBeInTheDocument();
  });

  it('limpa os dados em cache ao sair', async () => {
    vi.spyOn(api, 'refreshAccessToken').mockResolvedValue('token');
    vi.spyOn(authService, 'getMe').mockResolvedValue(me);
    const logout = vi.spyOn(authService, 'logout').mockResolvedValue();
    const client = renderWithAuth();
    await screen.findByText('status: authenticated');
    client.setQueryData(['users'], ['dado sensível']);

    await act(async () => screen.getByText('sair').click());
    expect(logout).toHaveBeenCalled();
    expect(screen.getByText('status: anonymous')).toBeInTheDocument();
    expect(client.getQueryData(['users'])).toBeUndefined();
  });

  it('volta ao login quando a sessão expira em outra requisição', async () => {
    let expire: () => void = () => {};
    vi.spyOn(api, 'refreshAccessToken').mockResolvedValue('token');
    vi.spyOn(authService, 'getMe').mockResolvedValue(me);
    vi.spyOn(api, 'onSessionExpired').mockImplementation((listener) => {
      expire = listener;
      return () => true;
    });
    renderWithAuth();
    await screen.findByText('status: authenticated');
    act(() => expire());
    expect(screen.getByText('status: anonymous')).toBeInTheDocument();
  });
});
