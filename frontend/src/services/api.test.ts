import { AxiosError, AxiosHeaders, type AxiosAdapter, type InternalAxiosRequestConfig } from 'axios';

import { api, ApiError, onSessionExpired, toApiError } from './api';
import { tokenStore } from './tokenStore';

function axiosErrorWith(status: number | null, data?: unknown) {
  const config = { headers: new AxiosHeaders() };
  const response =
    status === null ? undefined : { status, statusText: '', headers: {}, config, data };
  return new AxiosError('fail', 'ERR', config, null, response);
}

describe('toApiError', () => {
  it('usa a mensagem padronizada do backend', () => {
    const err = toApiError(
      axiosErrorWith(422, { detail: { code: 'validation_error', message: 'Dados inválidos.' } }),
    );
    expect(err).toBeInstanceOf(ApiError);
    expect(err.message).toBe('Dados inválidos.');
    expect(err.status).toBe(422);
    expect(err.code).toBe('validation_error');
  });

  it('identifica falha de rede', () => {
    expect(toApiError(axiosErrorWith(null)).code).toBe('network_error');
  });
});

// ---------- renovação automática da sessão ----------

type Handler = (config: InternalAxiosRequestConfig) => { status: number; data?: unknown };

function mockAdapter(handler: Handler) {
  const calls: { url: string; auth: string | undefined }[] = [];
  const adapter: AxiosAdapter = async (config) => {
    calls.push({ url: config.url ?? '', auth: config.headers?.Authorization as string | undefined });
    const { status, data } = handler(config);
    const response = { status, statusText: '', headers: {}, config, data, request: {} };
    if (status >= 400) throw new AxiosError('fail', 'ERR', config, {}, response);
    return response;
  };
  api.defaults.adapter = adapter;
  return calls;
}

describe('interceptor de sessão', () => {
  const originalAdapter = api.defaults.adapter;
  afterEach(() => {
    api.defaults.adapter = originalAdapter;
    tokenStore.set(null);
  });

  it('renova o token uma única vez para várias requisições com 401', async () => {
    tokenStore.set('velho');
    const calls = mockAdapter((config) => {
      if (config.url === '/auth/refresh') return { status: 200, data: { access_token: 'novo' } };
      const auth = config.headers?.Authorization;
      return auth === 'Bearer novo' ? { status: 200, data: { ok: true } } : { status: 401 };
    });

    const results = await Promise.all([api.get('/a'), api.get('/b'), api.get('/c')]);
    expect(results.map((r) => r.data.ok)).toEqual([true, true, true]);
    expect(calls.filter((c) => c.url === '/auth/refresh')).toHaveLength(1);
    expect(tokenStore.get()).toBe('novo');
  });

  it('encerra a sessão quando não consegue renovar', async () => {
    tokenStore.set('velho');
    const expired = vi.fn();
    const unsubscribe = onSessionExpired(expired);
    mockAdapter(() => ({ status: 401 }));

    await expect(api.get('/a')).rejects.toBeInstanceOf(AxiosError);
    expect(expired).toHaveBeenCalledTimes(1);
    expect(tokenStore.get()).toBeNull();
    unsubscribe();
  });

  it('não tenta renovar nas rotas de autenticação nem em outros erros', async () => {
    const calls = mockAdapter((config) => (config.url === '/auth/login' ? { status: 401 } : { status: 403 }));
    await expect(api.post('/auth/login', {}, { skipAuthRefresh: true })).rejects.toBeInstanceOf(AxiosError);
    await expect(api.get('/users')).rejects.toBeInstanceOf(AxiosError);
    expect(calls.map((c) => c.url)).toEqual(['/auth/login', '/users']);
  });
});
