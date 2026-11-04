import { fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';

import * as greenhouseService from '@/services/greenhouseService';
import * as historyService from '@/services/historyService';
import type { HistoryData } from '@/types/history';

import { HistoryPage } from './HistoryPage';

const thresholds = { temp_min: 16, temp_warning: 25, temp_critical: 26, humidity_min: 65, humidity_max: 85 };

function history(overrides: Partial<HistoryData> = {}): HistoryData {
  return {
    greenhouse_id: 1,
    period: '24h',
    granularity: 'raw',
    start: new Date(Date.now() - 86_400_000).toISOString(),
    end: new Date().toISOString(),
    timezone: 'America/Sao_Paulo',
    points: [
      {
        measured_at: new Date(Date.now() - 600_000).toISOString(),
        device_id: 'esp32-01',
        canopy_temperature: 22.5,
        canopy_humidity: 75,
        ceiling_temperature: 24,
        ceiling_humidity: 70,
      },
    ],
    days: [],
    thresholds,
    ...overrides,
  };
}

function renderPage(url = '/historico') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <HistoryPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('HistoryPage', () => {
  beforeEach(() => {
    vi.spyOn(greenhouseService, 'listGreenhouses').mockResolvedValue([{ id: 1, name: 'Estufa 01' }]);
  });
  afterEach(() => vi.restoreAllMocks());

  it('carrega as últimas 24 horas por padrão e mostra a tabela', async () => {
    const spy = vi.spyOn(historyService, 'getHistory').mockResolvedValue(history());
    renderPage();
    expect(await screen.findByText(/Últimas 24 horas · cada medição/)).toBeInTheDocument();
    expect(spy).toHaveBeenCalledWith(1, { period: '24h' });

    fireEvent.click(screen.getByRole('radio', { name: 'Tabela' }));
    expect(screen.getByText('22,5 °C')).toBeInTheDocument();
    expect(screen.getByText('Temperatura teto')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('radio', { name: 'Dossel' }));
    expect(screen.queryByText('Temperatura teto')).not.toBeInTheDocument();
  });

  it('troca para 7 dias', async () => {
    const spy = vi.spyOn(historyService, 'getHistory').mockResolvedValue(history());
    renderPage();
    await screen.findByText(/Últimas 24 horas/);
    spy.mockResolvedValue(history({ period: '7d', granularity: 'daily', points: [], days: [] }));
    fireEvent.click(screen.getByRole('radio', { name: '7 dias' }));
    expect(spy).toHaveBeenLastCalledWith(1, { period: '7d' });
    expect(await screen.findByText('Sem leituras neste período')).toBeInTheDocument();
  });

  it('valida o período personalizado antes de consultar', async () => {
    const spy = vi.spyOn(historyService, 'getHistory').mockResolvedValue(history());
    renderPage('/historico?periodo=custom');
    expect(await screen.findByText('Escolha o período')).toBeInTheDocument();
    expect(spy).not.toHaveBeenCalled();

    const [from] = screen.getAllByDisplayValue(/\d{4}-\d{2}-\d{2}/);
    fireEvent.change(from, { target: { value: '2020-01-01' } });
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar' }));
    expect(screen.getByRole('alert')).toHaveTextContent('no máximo 60 dias');
    expect(spy).not.toHaveBeenCalled();
  });

  it('usa as datas da URL', async () => {
    const spy = vi.spyOn(historyService, 'getHistory').mockResolvedValue(history({ period: 'custom' }));
    renderPage('/historico?periodo=custom&inicio=2026-03-01&fim=2026-03-02');
    await screen.findByText(/Período personalizado/);
    expect(spy).toHaveBeenCalledWith(1, { start: '2026-03-01', end: '2026-03-02' });
  });
});
