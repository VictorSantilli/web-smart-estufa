import { fireEvent, render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';

import * as detectionService from '@/services/detectionService';
import * as greenhouseService from '@/services/greenhouseService';
import type { Page } from '@/types/api';
import type { Detection } from '@/types/detection';

import { DetectionsPage } from './DetectionsPage';

function detection(overrides: Partial<Detection> = {}): Detection {
  return {
    id: 1,
    greenhouse_id: 1,
    detected_at: '2026-11-04T01:08:57Z',
    recorded_at: '2026-11-04T01:09:02Z',
    detection_class: 'fungico',
    confidence: 0.9123,
    probabilities: { fungal: 0.9123, bacterial: 0.05, healthy: 0.0377, lettuce: 0.99 },
    pathogen_detected: true,
    alert: true,
    status: 'pending',
    has_heatmap: false,
    bbox: null,
    model_version: 'mobilenet-v3',
    domain_model_version: 'alface-v1',
    inference_ms: 123.4,
    verification_ms: 10,
    ...overrides,
  };
}

function page(items: Detection[], total = items.length, pageNumber = 1): Page<Detection> {
  return { items, total, page: pageNumber, page_size: 24 };
}

function renderPage(url = '/deteccoes') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <DetectionsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('DetectionsPage', () => {
  beforeEach(() => {
    vi.spyOn(greenhouseService, 'listGreenhouses').mockResolvedValue([{ id: 1, name: 'Estufa 01' }]);
    vi.spyOn(detectionService, 'getDetectionImage').mockResolvedValue(new Blob(['x'], { type: 'image/jpeg' }));
    URL.createObjectURL = vi.fn(() => 'blob:foto');
    URL.revokeObjectURL = vi.fn();
  });
  afterEach(() => vi.restoreAllMocks());

  it('lista as detecções com foto, resultado, confiança e hora de Brasília', async () => {
    const spy = vi
      .spyOn(detectionService, 'listDetections')
      .mockResolvedValue(page([detection(), detection({ id: 2, detection_class: 'saudavel', alert: false, confidence: 0.98 })]));
    renderPage();
    expect(await screen.findByText('2 detecções')).toBeInTheDocument();
    expect(spy).toHaveBeenCalledWith(1, { page: 1, page_size: 24 });
    const card = screen.getByRole('button', { name: /Detecção de 03\/11\/2026, 22:08: Fúngico/ });
    expect(within(card).getByText('91,2%')).toBeInTheDocument();
    expect(within(card).getByText('Alerta')).toBeInTheDocument();
    expect(screen.getByText('Saudável', { selector: 'span' })).toBeInTheDocument();
    const images = await screen.findAllByRole('img', { name: /Foto analisada/ });
    expect(images[0]).toHaveAttribute('src', 'blob:foto');
  });

  it('filtra pelo resultado da IA e pelas datas', async () => {
    const spy = vi.spyOn(detectionService, 'listDetections').mockResolvedValue(page([detection()]));
    renderPage();
    await screen.findByText('1 detecção');
    fireEvent.click(screen.getByRole('radio', { name: 'Bacteriano' }));
    expect(spy).toHaveBeenLastCalledWith(1, { page: 1, page_size: 24, class: 'bacteriano' });
    fireEvent.change(screen.getByLabelText('De'), { target: { value: '2026-11-01' } });
    fireEvent.change(screen.getByLabelText('Até'), { target: { value: '2026-11-03' } });
    expect(spy).toHaveBeenLastCalledWith(1, {
      page: 1,
      page_size: 24,
      class: 'bacteriano',
      start: '2026-11-01',
      end: '2026-11-03',
    });
    fireEvent.click(screen.getByRole('button', { name: 'Limpar datas' }));
    expect(screen.getByLabelText('De')).toHaveValue('');
    expect(screen.queryByRole('button', { name: 'Limpar datas' })).not.toBeInTheDocument();
  });

  it('avisa quando a data inicial é depois da final', async () => {
    vi.spyOn(detectionService, 'listDetections').mockResolvedValue(page([]));
    renderPage('/deteccoes?inicio=2026-11-05&fim=2026-11-01');
    expect(await screen.findByText('A data inicial deve ser anterior à data final.')).toBeInTheDocument();
  });

  it('pagina os resultados', async () => {
    const spy = vi.spyOn(detectionService, 'listDetections').mockResolvedValue(page([detection()], 30));
    renderPage();
    expect(await screen.findByText('Página 1 de 2')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Próxima página' }));
    expect(spy).toHaveBeenLastCalledWith(1, { page: 2, page_size: 24 });
  });

  it('abre o detalhe com as probabilidades', async () => {
    vi.spyOn(detectionService, 'listDetections').mockResolvedValue(page([detection()]));
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: /Fúngico/ }));
    const dialog = screen.getByRole('dialog', { name: 'Detecção da IA' });
    expect(within(dialog).getByText('Probabilidade de cada classe')).toBeInTheDocument();
    expect(within(dialog).getByText('99%')).toBeInTheDocument();
    expect(within(dialog).getByText('mobilenet-v3')).toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Fechar' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('mostra quando não há detecções', async () => {
    vi.spyOn(detectionService, 'listDetections').mockResolvedValue(page([]));
    renderPage();
    expect(await screen.findByText('Nenhuma detecção encontrada')).toBeInTheDocument();
  });

  it('mostra imagem indisponível quando o blob falha', async () => {
    vi.spyOn(detectionService, 'listDetections').mockResolvedValue(page([detection()]));
    vi.spyOn(detectionService, 'getDetectionImage').mockRejectedValue(new Error('404'));
    renderPage();
    expect(await screen.findByText('Imagem indisponível', {}, { timeout: 4000 })).toBeInTheDocument();
  });

  it('mostra erro da API', async () => {
    vi.spyOn(detectionService, 'listDetections').mockRejectedValue(new Error('falhou'));
    renderPage();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
