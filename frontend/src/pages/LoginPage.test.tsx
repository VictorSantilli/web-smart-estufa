import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { AxiosError, AxiosHeaders } from 'axios';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { AuthContext, type AuthContextValue } from '@/contexts/authContextValue';

import { LoginPage } from './LoginPage';

function renderLogin(login: AuthContextValue['login']) {
  const value: AuthContextValue = { status: 'anonymous', user: null, login, logout: vi.fn() };
  return render(
    <AuthContext.Provider value={value}>
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<p>dashboard</p>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

function fill(email: string, password: string) {
  fireEvent.change(screen.getByLabelText('E-mail'), { target: { value: email } });
  fireEvent.change(screen.getByLabelText('Senha'), { target: { value: password } });
  fireEvent.click(screen.getByRole('button', { name: /entrar/i }));
}

describe('LoginPage', () => {
  it('valida os campos antes de chamar a API', () => {
    const login = vi.fn();
    renderLogin(login);
    fill('', '');
    expect(screen.getByText('Informe o e-mail.')).toBeInTheDocument();
    expect(screen.getByText('Informe a senha.')).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();
  });

  it('mostra a mensagem de credenciais inválidas vinda do backend', async () => {
    const config = { headers: new AxiosHeaders() };
    const login = vi.fn().mockRejectedValue(
      new AxiosError('401', 'ERR', config, null, {
        status: 401,
        statusText: '',
        headers: {},
        config,
        data: { detail: { code: 'invalid_credentials', message: 'E-mail ou senha inválidos.' } },
      }),
    );
    renderLogin(login);
    fill('ana@estufa.com', 'errada');
    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou senha inválidos.');
  });

  it('redireciona para o Dashboard após login', async () => {
    const login = vi.fn().mockResolvedValue(undefined);
    renderLogin(login);
    fill('ana@estufa.com', 'Senha123');
    await waitFor(() => expect(screen.getByText('dashboard')).toBeInTheDocument());
    expect(login).toHaveBeenCalledWith('ana@estufa.com', 'Senha123');
  });
});
