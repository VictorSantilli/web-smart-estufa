import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { LineChart, RefreshCw, Sprout } from 'lucide-react';

import {
  type Metric,
  type Sensor,
  formatDay,
  hasAnyData,
  METRICS,
  toChartRows,
} from '@/components/history/chartData';
import { CustomRangeForm } from '@/components/history/CustomRangeForm';
import { HistoryChart, HistoryLegend } from '@/components/history/HistoryChart';
import { HistoryTable } from '@/components/history/HistoryTable';
import { GreenhouseSelector } from '@/components/greenhouse/GreenhouseSelector';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { SegmentedControl } from '@/components/ui/SegmentedControl';
import { Spinner } from '@/components/ui/Spinner';
import { config } from '@/config';
import { useHistory } from '@/hooks/useHistory';
import { useSelectedGreenhouse } from '@/hooks/useSelectedGreenhouse';
import { toApiError } from '@/services/api';
import type { HistoryData, HistoryQuery, PresetPeriod } from '@/types/history';
import { cn } from '@/utils/cn';

type PeriodOption = PresetPeriod | 'custom';
type MetricView = Metric | 'both';
type SensorView = Sensor | 'both';
type Display = 'chart' | 'table';

const periodOptions: { value: PeriodOption; label: string }[] = [
  { value: '24h', label: '24 horas' },
  { value: '7d', label: '7 dias' },
  { value: '30d', label: '30 dias' },
  { value: 'custom', label: 'Personalizado' },
];
const metricOptions: { value: MetricView; label: string }[] = [
  { value: 'temperature', label: 'Temperatura' },
  { value: 'humidity', label: 'Umidade' },
  { value: 'both', label: 'Conjunto' },
];
const sensorOptions: { value: SensorView; label: string }[] = [
  { value: 'both', label: 'Ambos' },
  { value: 'canopy', label: 'Dossel' },
  { value: 'ceiling', label: 'Teto' },
];
const displayOptions: { value: Display; label: string }[] = [
  { value: 'chart', label: 'Gráfico' },
  { value: 'table', label: 'Tabela' },
];

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

/** Período escolhido, guardado na URL (?periodo=7d ou ?inicio=...&fim=...) para poder ser compartilhado. */
function usePeriodParams() {
  const [params, setParams] = useSearchParams();
  const start = params.get('inicio') ?? '';
  const end = params.get('fim') ?? '';
  const raw = params.get('periodo');
  const period: PeriodOption = raw === '7d' || raw === '30d' || raw === 'custom' ? raw : '24h';

  const query: HistoryQuery | null =
    period !== 'custom' ? { period } : DATE_RE.test(start) && DATE_RE.test(end) ? { start, end } : null;

  const update = (values: Record<string, string | null>) =>
    setParams(
      (current) => {
        for (const [key, value] of Object.entries(values)) {
          if (value === null) current.delete(key);
          else current.set(key, value);
        }
        return current;
      },
      { replace: true },
    );

  return {
    period,
    start,
    end,
    query,
    setPeriod: (p: PeriodOption) => update({ periodo: p === '24h' ? null : p, ...(p !== 'custom' && { inicio: null, fim: null }) }),
    setRange: (s: string, e: string) => update({ periodo: 'custom', inicio: s, fim: e }),
  };
}

function describe(data: HistoryData): string {
  const what = data.granularity === 'raw' ? 'cada medição' : 'máxima, média e mínima por dia';
  if (data.period === '24h') return `Últimas 24 horas · ${what}`;
  if (data.period === '7d') return `Últimos 7 dias · ${what}`;
  if (data.period === '30d') return `Últimos 30 dias · ${what}`;
  if (data.granularity === 'daily') {
    const first = data.days[0]?.date;
    const last = data.days[data.days.length - 1]?.date;
    return `${first ? formatDay(first) : ''} a ${last ? formatDay(last) : ''} · ${what}`;
  }
  return `Período personalizado · ${what}`;
}

export function HistoryPage() {
  const { greenhouses, selected, select } = useSelectedGreenhouse();
  const { period, start, end, query, setPeriod, setRange } = usePeriodParams();
  const history = useHistory(selected?.id ?? null, query);
  const [metricView, setMetricView] = useState<MetricView>('temperature');
  const [sensorView, setSensorView] = useState<SensorView>('both');
  const [display, setDisplay] = useState<Display>('chart');

  const data = history.data;
  const rows = useMemo(() => (data ? toChartRows(data) : []), [data]);
  const metrics: Metric[] = metricView === 'both' ? ['temperature', 'humidity'] : [metricView];
  const sensors: Sensor[] = sensorView === 'both' ? ['canopy', 'ceiling'] : [sensorView];

  const header = (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Histórico</h1>
        <p className="text-sm text-gray-500">Evolução da temperatura e da umidade (horário de Brasília).</p>
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

  const range: [number, number] = data ? [Date.parse(data.start), Math.min(Date.parse(data.end), Date.now())] : [0, 0];

  return (
    <div className="space-y-5">
      {header}

      <div className="space-y-3">
        <SegmentedControl label="Período" value={period} options={periodOptions} onChange={setPeriod} />
        {period === 'custom' && (
          <CustomRangeForm
            key={`${start}-${end}`}
            initialStart={start || undefined}
            initialEnd={end || undefined}
            maxDays={config.historyMaxDays}
            onApply={setRange}
          />
        )}
        <div className="flex flex-wrap items-center gap-2">
          <SegmentedControl label="Grandeza" value={metricView} options={metricOptions} onChange={setMetricView} />
          <SegmentedControl label="Sensores" value={sensorView} options={sensorOptions} onChange={setSensorView} />
          <SegmentedControl label="Exibição" value={display} options={displayOptions} onChange={setDisplay} />
        </div>
      </div>

      {!query ? (
        <EmptyState
          icon={<LineChart className="h-10 w-10" aria-hidden />}
          title="Escolha o período"
          description="Informe a data inicial e a data final e clique em Aplicar."
        />
      ) : history.isPending ? (
        <Spinner label="Carregando histórico..." />
      ) : history.isError ? (
        <ErrorState message={toApiError(history.error).message} onRetry={() => history.refetch()} />
      ) : !hasAnyData(data!) ? (
        <EmptyState
          icon={<LineChart className="h-10 w-10" aria-hidden />}
          title="Sem leituras neste período"
          description="A estufa não enviou dados no intervalo escolhido. Tente outro período."
        />
      ) : (
        <section className={cn('space-y-4 transition-opacity', history.isFetching && history.isPlaceholderData && 'opacity-60')}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-gray-600">{describe(data!)}</p>
            {display === 'chart' && <HistoryLegend sensors={sensors} granularity={data!.granularity} />}
          </div>

          {display === 'table' ? (
            <HistoryTable data={data!} metrics={metrics} sensors={sensors} />
          ) : (
            <div className="grid gap-4">
              {metrics.map((metric) => (
                <figure key={metric} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                  <figcaption className="mb-2 text-sm font-medium text-gray-700">
                    {METRICS[metric].label} ({METRICS[metric].unit})
                  </figcaption>
                  <HistoryChart
                    rows={rows}
                    metric={metric}
                    sensors={sensors}
                    granularity={data!.granularity}
                    thresholds={data!.thresholds}
                    range={range}
                    syncId={metrics.length > 1 ? 'history' : undefined}
                    height={metrics.length > 1 ? 240 : 320}
                  />
                </figure>
              ))}
            </div>
          )}

          {period === '24h' && (
            <p className="flex items-center gap-1.5 text-xs text-gray-400">
              <RefreshCw className={cn('h-3 w-3', history.isFetching && 'animate-spin')} aria-hidden />
              As últimas 24 horas se atualizam a cada minuto.
            </p>
          )}
        </section>
      )}
    </div>
  );
}
