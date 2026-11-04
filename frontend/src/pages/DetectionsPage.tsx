import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { ChevronLeft, ChevronRight, ScanSearch, Sprout } from 'lucide-react';

import { DetectionCard } from '@/components/detections/DetectionCard';
import { DetectionDetail } from '@/components/detections/DetectionDetail';
import { GreenhouseSelector } from '@/components/greenhouse/GreenhouseSelector';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { SegmentedControl } from '@/components/ui/SegmentedControl';
import { Spinner } from '@/components/ui/Spinner';
import { useDetections } from '@/hooks/useDetections';
import { useSelectedGreenhouse } from '@/hooks/useSelectedGreenhouse';
import { toApiError } from '@/services/api';
import type { Detection, DetectionClass, DetectionQuery } from '@/types/detection';
import { cn } from '@/utils/cn';

const PAGE_SIZE = 24;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

type ClassFilter = DetectionClass | 'all';

const classOptions: { value: ClassFilter; label: string }[] = [
  { value: 'all', label: 'Todas' },
  { value: 'saudavel', label: 'Saudável' },
  { value: 'fungico', label: 'Fúngico' },
  { value: 'bacteriano', label: 'Bacteriano' },
  { value: 'nao_alface', label: 'Não é alface' },
];

/** Filtros na URL (?resultado=fungico&inicio=...&fim=...&pagina=2), para poder compartilhar o link. */
function useDetectionParams() {
  const [params, setParams] = useSearchParams();
  const rawClass = params.get('resultado');
  const detectionClass: ClassFilter =
    rawClass === 'saudavel' || rawClass === 'fungico' || rawClass === 'bacteriano' || rawClass === 'nao_alface'
      ? rawClass
      : 'all';
  const start = params.get('inicio') ?? '';
  const end = params.get('fim') ?? '';
  const page = Math.max(1, Number(params.get('pagina')) || 1);

  const query: DetectionQuery = {
    page,
    page_size: PAGE_SIZE,
    ...(detectionClass !== 'all' && { class: detectionClass }),
    ...(DATE_RE.test(start) && { start }),
    ...(DATE_RE.test(end) && { end }),
  };

  const update = (values: Record<string, string | null>) =>
    setParams(
      (current) => {
        for (const [key, value] of Object.entries(values)) {
          if (value === null || value === '') current.delete(key);
          else current.set(key, value);
        }
        return current;
      },
      { replace: true },
    );

  return {
    detectionClass,
    start,
    end,
    page,
    query,
    setClass: (c: ClassFilter) => update({ resultado: c === 'all' ? null : c, pagina: null }),
    setDates: (s: string, e: string) => update({ inicio: s, fim: e, pagina: null }),
    setPage: (p: number) => update({ pagina: p === 1 ? null : String(p) }),
  };
}

export function DetectionsPage() {
  const { greenhouses, selected, select } = useSelectedGreenhouse();
  const { detectionClass, start, end, page, query, setClass, setDates, setPage } = useDetectionParams();
  const detections = useDetections(selected?.id ?? null, query);
  const [open, setOpen] = useState<Detection | null>(null);

  const header = (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Detecções da IA</h1>
        <p className="text-sm text-gray-500">Fotos analisadas pela IA e o resultado de cada uma (horário de Brasília).</p>
      </div>
      {greenhouses.data && (
        <GreenhouseSelector greenhouses={greenhouses.data} selectedId={selected?.id ?? null} onSelect={select} />
      )}
    </div>
  );

  if (greenhouses.isPending) return <div className="space-y-6">{header}<Spinner /></div>;
  if (greenhouses.isError) {
    return (
      <div className="space-y-6">
        {header}
        <ErrorState message={toApiError(greenhouses.error).message} onRetry={() => greenhouses.refetch()} />
      </div>
    );
  }
  if (!selected) {
    return (
      <div className="space-y-6">
        {header}
        <EmptyState
          icon={<Sprout className="h-10 w-10" aria-hidden />}
          title="Nenhuma estufa disponível"
          description="Você ainda não tem acesso a nenhuma estufa. Peça ao administrador para liberar o acesso."
        />
      </div>
    );
  }

  const data = detections.data;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const invalidRange = DATE_RE.test(start) && DATE_RE.test(end) && start > end;

  return (
    <div className="space-y-5">
      {header}

      <div className="flex flex-wrap items-end gap-3">
        <SegmentedControl label="Resultado" value={detectionClass} options={classOptions} onChange={setClass} />
        <label className="flex flex-col text-xs font-medium text-gray-600">
          De
          <input
            type="date"
            value={start}
            onChange={(event) => setDates(event.target.value, end)}
            className="mt-1 rounded-lg border border-gray-300 px-2 py-1 text-sm text-gray-800"
          />
        </label>
        <label className="flex flex-col text-xs font-medium text-gray-600">
          Até
          <input
            type="date"
            value={end}
            onChange={(event) => setDates(start, event.target.value)}
            className="mt-1 rounded-lg border border-gray-300 px-2 py-1 text-sm text-gray-800"
          />
        </label>
        {(start || end) && (
          <Button variant="secondary" onClick={() => setDates('', '')}>
            Limpar datas
          </Button>
        )}
      </div>

      {invalidRange ? (
        <ErrorState message="A data inicial deve ser anterior à data final." />
      ) : detections.isPending ? (
        <Spinner label="Carregando detecções..." />
      ) : detections.isError ? (
        <ErrorState message={toApiError(detections.error).message} onRetry={() => detections.refetch()} />
      ) : data!.items.length === 0 ? (
        <EmptyState
          icon={<ScanSearch className="h-10 w-10" aria-hidden />}
          title="Nenhuma detecção encontrada"
          description="A IA ainda não analisou fotos desta estufa com estes filtros."
        />
      ) : (
        <section className={cn('space-y-4 transition-opacity', detections.isFetching && detections.isPlaceholderData && 'opacity-60')}>
          <p className="text-sm text-gray-600">
            {data!.total} {data!.total === 1 ? 'detecção' : 'detecções'}
          </p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {data!.items.map((detection) => (
              <DetectionCard key={detection.id} detection={detection} onOpen={setOpen} />
            ))}
          </div>
          {totalPages > 1 && (
            <nav className="flex items-center justify-center gap-3" aria-label="Paginação">
              <Button variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)} aria-label="Página anterior">
                <ChevronLeft className="h-4 w-4" aria-hidden />
              </Button>
              <span className="text-sm text-gray-600">
                Página {page} de {totalPages}
              </span>
              <Button
                variant="secondary"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                aria-label="Próxima página"
              >
                <ChevronRight className="h-4 w-4" aria-hidden />
              </Button>
            </nav>
          )}
        </section>
      )}

      <DetectionDetail detection={open} onClose={() => setOpen(null)} />
    </div>
  );
}
