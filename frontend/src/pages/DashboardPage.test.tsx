import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';

import * as dashboardService from '@/services/dashboardService';
import * as greenhouseService from '@/services/greenhouseService';
import type { DashboardData } from '@/types/dashboard';

import { DashboardPage } from './DashboardPage';

const now = new Date().toISOString();

function dashboard(overrides: Partial<DashboardData> = {}): DashboardData {
  const m = (value: number, level: 'ok' | 'warning' | 'critical' | 'low') => ({
    value,
    level,
    measured_at: now,
    is_current: true,
  });
  return {
    greenhouse: { id: 1, name: 'Estufa 01' },
    has_data: true,
    last_reading_at: now,
    last_communication_at: now,
    is_online: true,
    stale_after_minutes: 15,
    canopy: { ok: true, temperature: m(25.5, 'warning'), humidity: m(70, 'ok') },
    ceiling: { ok: true, temperature: m(27, 'critical'), humidity: m(60, 'low') },
    fans: { state: 'on', measured_at: now },
    thresholds: { temp_min: 16, temp_warning: 25, temp_critical: 26, humidity_min: 65, humidity_max: 85 },
    generated_at: now,
    ...overrides,
  };
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('DashboardPage', () => {
  afterEach(() => vi.restoreAllMocks());

  it('mostra indicadores com faixas destacadas', async () => {
    vi.spyOn(greenhouseService, 'listGreenhouses').mockResolvedValue([{ id: 1, name: 'Estufa 01' }]);
    vi.spyOn(dashboardService, 'getDashboard').mockResolvedValue(dashboard());
    renderPage();
    expect(await screen.findByText('Acima do ideal')).toBeInTheDocument();
    expect(screen.getByText('Crítico')).toBeInTheDocument();
    expect(screen.getByText('Abaixo do ideal')).toBeInTheDocument();
    expect(screen.getByText('Online')).toBeInTheDocument();
    expect(screen.getByText('Ligadas')).toBeInTheDocument();
    // Só uma estufa: sem seletor
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
  });

  it('alerta quando os dados estão desatualizados', async () => {
    vi.spyOn(greenhouseService, 'listGreenhouses').mockResolvedValue([{ id: 1, name: 'Estufa 01' }]);
    vi.spyOn(dashboardService, 'getDashboard').mockResolvedValue(dashboard({ is_online: false }));
    renderPage();
    expect(await screen.findByText('Dados desatualizados.')).toBeInTheDocument();
    expect(screen.getByText('Offline')).toBeInTheDocument();
  });

  it('mostra mensagem quando não há dados', async () => {
    vi.spyOn(greenhouseService, 'listGreenhouses').mockResolvedValue([{ id: 1, name: 'Estufa 01' }]);
    vi.spyOn(dashboardService, 'getDashboard').mockResolvedValue(dashboard({ has_data: false }));
    renderPage();
    expect(await screen.findByText('Ainda não há dados desta estufa')).toBeInTheDocument();
  });

  it('mostra seletor quando há mais de uma estufa', async () => {
    vi.spyOn(greenhouseService, 'listGreenhouses').mockResolvedValue([
      { id: 1, name: 'Estufa 01' },
      { id: 2, name: 'Estufa 02' },
    ]);
    vi.spyOn(dashboardService, 'getDashboard').mockResolvedValue(dashboard());
    renderPage();
    expect(await screen.findByRole('combobox')).toBeInTheDocument();
  });

  it('avisa quando o usuário não tem estufas', async () => {
    vi.spyOn(greenhouseService, 'listGreenhouses').mockResolvedValue([]);
    renderPage();
    expect(await screen.findByText('Nenhuma estufa disponível')).toBeInTheDocument();
  });

  it('indica sensor com falha e último valor válido', async () => {
    vi.spyOn(greenhouseService, 'listGreenhouses').mockResolvedValue([{ id: 1, name: 'Estufa 01' }]);
    const data = dashboard();
    data.canopy = { ...data.canopy, ok: false, temperature: { ...data.canopy.temperature, is_current: false } };
    vi.spyOn(dashboardService, 'getDashboard').mockResolvedValue(data);
    renderPage();
    expect(await screen.findByText('Falha: Dossel')).toBeInTheDocument();
    expect(screen.getByText(/Último valor válido/)).toBeInTheDocument();
  });
});
