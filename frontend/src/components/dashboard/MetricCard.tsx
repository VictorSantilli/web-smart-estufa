import { Droplets, Thermometer } from 'lucide-react';

import type { Measurement, Thresholds } from '@/types/dashboard';
import { cn } from '@/utils/cn';
import { formatDateTime } from '@/utils/datetime';

import { levelLabel, levelStyles, rangeHint } from './levels';

interface MetricCardProps {
  kind: 'temperature' | 'humidity';
  position: string; // "Dossel" | "Teto"
  measurement: Measurement;
  thresholds: Thresholds;
}

const numberFormat = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });

export function MetricCard({ kind, position, measurement, thresholds }: MetricCardProps) {
  const { value, level, measured_at, is_current } = measurement;
  const style = level ? levelStyles[level] : null;
  const Icon = kind === 'temperature' ? Thermometer : Droplets;
  const title = kind === 'temperature' ? 'Temperatura' : 'Umidade';
  const unit = kind === 'temperature' ? '°C' : '%';

  return (
    <section
      aria-label={`${title} · ${position}`}
      className={cn('rounded-xl border p-5 shadow-sm transition-colors', style?.card ?? 'border-gray-200 bg-white')}
    >
      <header className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-600">
          <span
            className={cn(
              'flex h-8 w-8 items-center justify-center rounded-lg',
              kind === 'temperature' ? 'bg-amber-100 text-amber-700' : 'bg-sky-100 text-sky-700',
            )}
          >
            <Icon className="h-4 w-4" aria-hidden />
          </span>
          <span>
            {title}
            <span className="block text-xs font-normal text-gray-500">{position}</span>
          </span>
        </div>
        {level && (
          <span className={cn('shrink-0 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium', levelStyles[level].badge)}>
            {levelLabel(level, kind)}
          </span>
        )}
      </header>

      <p className={cn('mt-4 text-4xl font-semibold tabular-nums', style?.value ?? 'text-gray-300')}>
        {value === null ? '--' : numberFormat.format(value)}
        <span className="ml-1 text-xl font-medium">{unit}</span>
      </p>

      <p className="mt-2 text-xs text-gray-500">{rangeHint(kind, thresholds)}</p>
      {measured_at && (
        <p className={cn('mt-1 text-xs', is_current ? 'text-gray-500' : 'font-medium text-orange-700')}>
          {is_current ? 'Medido em ' : 'Último valor válido: '}
          {formatDateTime(measured_at)}
        </p>
      )}
      {!measured_at && <p className="mt-1 text-xs text-gray-500">Sem leituras deste sensor</p>}
    </section>
  );
}
