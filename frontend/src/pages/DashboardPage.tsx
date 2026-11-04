import { useState } from 'react';

import { Activity, Clock, Cpu, Fan, RefreshCw, Sprout, Wifi, WifiOff } from 'lucide-react';

import { MetricCard } from '@/components/dashboard/MetricCard';
import { StatusCard } from '@/components/dashboard/StatusCard';
import { GreenhouseSelector } from '@/components/greenhouse/GreenhouseSelector';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { SegmentedControl } from '@/components/ui/SegmentedControl';
import { Spinner } from '@/components/ui/Spinner';
import { useDashboard } from '@/hooks/useDashboard';
import { useSelectedGreenhouse } from '@/hooks/useSelectedGreenhouse';
import { toApiError } from '@/services/api';
import type { DashboardData } from '@/types/dashboard';
import { cn } from '@/utils/cn';
import { formatDateTime, formatRelative } from '@/utils/datetime';

type SensorView = 'both' | 'canopy' | 'ceiling';

const viewOptions: { value: SensorView; label: string }[] = [
  { value: 'both', label: 'Ambos' },
  { value: 'canopy', label: 'Dossel' },
  { value: 'ceiling', label: 'Teto' },
];

function SensorViewToggle({ value, onChange }: { value: SensorView; onChange: (v: SensorView) => void }) {
  return <SegmentedControl label="Sensores exibidos" value={value} options={viewOptions} onChange={onChange} />;
}

function EnvironmentSection({ data, view }: { data: DashboardData; view: SensorView }) {
  const sensors = [
    { key: 'canopy' as const, label: 'Dossel', status: data.canopy },
    { key: 'ceiling' as const, label: 'Teto', status: data.ceiling },
  ].filter((s) => view === 'both' || view === s.key);

  return (
    <div className={cn('grid gap-4', view === 'both' ? 'sm:grid-cols-2 xl:grid-cols-4' : 'sm:grid-cols-2')}>
      {sensors.map((s) => (
        <MetricCard key={`${s.key}-t`} kind="temperature" position={s.label} measurement={s.status.temperature} thresholds={data.thresholds} />
      ))}
      {sensors.map((s) => (
        <MetricCard key={`${s.key}-h`} kind="humidity" position={s.label} measurement={s.status.humidity} thresholds={data.thresholds} />
      ))}
    </div>
  );
}

function SystemSection({ data }: { data: DashboardData }) {
  const failed = [!data.canopy.ok && 'Dossel', !data.ceiling.ok && 'Teto'].filter(Boolean) as string[];
  const fans = {
    on: { tone: 'ok' as const, status: 'Ligadas' },
    off: { tone: 'neutral' as const, status: 'Desligadas' },
    unknown: { tone: 'neutral' as const, status: 'Sem informação' },
  }[data.fans.state];

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatusCard
        title="Sistema"
        icon={data.is_online ? <Wifi className="h-5 w-5" /> : <WifiOff className="h-5 w-5" />}
        tone={data.is_online ? 'ok' : 'critical'}
        status={data.is_online ? 'Online' : 'Offline'}
      >
        <p>{data.is_online ? 'Recebendo dados normalmente.' : `Sem dados há mais de ${data.stale_after_minutes} min.`}</p>
      </StatusCard>

      <StatusCard title="Última comunicação" icon={<Clock className="h-5 w-5" />} tone={data.is_online ? 'ok' : 'warning'} status={data.last_communication_at ? formatRelative(data.last_communication_at) : '—'}>
        {data.last_communication_at && <p>{formatDateTime(data.last_communication_at)}</p>}
        {data.last_reading_at && <p>Última medição: {formatDateTime(data.last_reading_at)}</p>}
      </StatusCard>

      <StatusCard
        title="Sensores"
        icon={<Cpu className="h-5 w-5" />}
        tone={failed.length === 0 ? 'ok' : failed.length === 2 ? 'critical' : 'warning'}
        status={failed.length === 0 ? 'Comunicando' : `Falha: ${failed.join(' e ')}`}
      >
        <p>Dossel: {data.canopy.ok ? 'OK' : 'sem leitura'} · Teto: {data.ceiling.ok ? 'OK' : 'sem leitura'}</p>
      </StatusCard>

      <StatusCard title="Ventoinhas" icon={<Fan className={cn('h-5 w-5', data.fans.state === 'on' && 'animate-spin [animation-duration:3s]')} />} tone={fans.tone} status={fans.status}>
        {data.fans.state === 'unknown' ? <p>O estado não foi registrado na última leitura.</p> : <p>Estado na última leitura.</p>}
      </StatusCard>
    </div>
  );
}

export function DashboardPage() {
  const { greenhouses, selected, select } = useSelectedGreenhouse();
  const dashboard = useDashboard(selected?.id ?? null);
  const [view, setView] = useState<SensorView>('both');

  const header = (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500">Situação atual da estufa, atualizada a cada minuto.</p>
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

  const data = dashboard.data;
  return (
    <div className="space-y-6">
      {header}

      {dashboard.isPending ? (
        <Spinner label="Carregando indicadores..." />
      ) : dashboard.isError ? (
        <ErrorState message={toApiError(dashboard.error).message} onRetry={() => dashboard.refetch()} />
      ) : !data!.has_data ? (
        <EmptyState
          icon={<Activity className="h-10 w-10" aria-hidden />}
          title="Ainda não há dados desta estufa"
          description="Assim que o ESP32 enviar a primeira leitura, a temperatura e a umidade aparecerão aqui."
        />
      ) : (
        <>
          {!data!.is_online && (
            <div role="alert" className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
              <WifiOff className="mt-0.5 h-5 w-5 shrink-0" aria-hidden />
              <p>
                <strong>Dados desatualizados.</strong> A estufa não envia dados há mais de {data!.stale_after_minutes} minutos
                {data!.last_communication_at && ` (último contato ${formatRelative(data!.last_communication_at)})`}. Verifique
                a energia e a conexão Wi-Fi do ESP32.
              </p>
            </div>
          )}

          <section className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-base font-semibold text-gray-800">Condições ambientais</h2>
              <SensorViewToggle value={view} onChange={setView} />
            </div>
            <EnvironmentSection data={data!} view={view} />
          </section>

          <section className="space-y-3">
            <h2 className="text-base font-semibold text-gray-800">Situação do sistema</h2>
            <SystemSection data={data!} />
          </section>

          <p className="flex items-center gap-1.5 text-xs text-gray-400">
            <RefreshCw className={cn('h-3 w-3', dashboard.isFetching && 'animate-spin')} aria-hidden />
            Atualizado {formatRelative(new Date(dashboard.dataUpdatedAt).toISOString())}
          </p>
        </>
      )}
    </div>
  );
}
