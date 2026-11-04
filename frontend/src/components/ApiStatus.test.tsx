import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import * as healthService from '@/services/healthService';

import { ApiStatus } from './ApiStatus';

function renderWithClient() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ApiStatus />
    </QueryClientProvider>,
  );
}

describe('ApiStatus', () => {
  afterEach(() => vi.restoreAllMocks());

  it('mostra servidor online quando a API e o banco respondem', async () => {
    vi.spyOn(healthService, 'getHealth').mockResolvedValue({
      status: 'ok',
      database: 'ok',
      version: '0.1.0',
      environment: 'test',
    });
    renderWithClient();
    expect(await screen.findByText('Servidor online · v0.1.0')).toBeInTheDocument();
  });

  it('avisa quando o banco está indisponível', async () => {
    vi.spyOn(healthService, 'getHealth').mockResolvedValue({
      status: 'degraded',
      database: 'unavailable',
      version: '0.1.0',
      environment: 'test',
    });
    renderWithClient();
    expect(await screen.findByText('Banco de dados indisponível')).toBeInTheDocument();
  });
});
