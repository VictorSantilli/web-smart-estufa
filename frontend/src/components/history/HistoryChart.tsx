import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TooltipProps } from 'recharts';

import type { Thresholds } from '@/types/dashboard';
import type { Granularity } from '@/types/history';

import {
  type ChartRow,
  formatDay,
  localHour,
  formatInstant,
  formatTick,
  formatValue,
  METRICS,
  type Metric,
  type Sensor,
  SENSORS,
  seriesKey,
  yDomain,
} from './chartData';

interface Reference {
  value: number;
  label: string;
  color: string;
  /** Rótulo abaixo da linha (evita sobreposição de linhas próximas, como 25 e 26 °C). */
  below?: boolean;
}

function references(metric: Metric, t: Thresholds): Reference[] {
  // Cores de status (reservadas para as faixas), sempre acompanhadas de rótulo.
  return metric === 'temperature'
    ? [
        { value: t.temp_min, label: `mín ${t.temp_min} °C`, color: '#3b82f6', below: true },
        { value: t.temp_warning, label: `atenção ${t.temp_warning} °C`, color: '#f97316', below: true },
        { value: t.temp_critical, label: `crítico ${t.temp_critical} °C`, color: '#dc2626' },
      ]
    : [
        { value: t.humidity_min, label: `mín ${t.humidity_min} %`, color: '#3b82f6', below: true },
        { value: t.humidity_max, label: `fungos ${t.humidity_max} %`, color: '#f97316' },
      ];
}

/** Marcas do eixo em horas cheias (a cada `step` horas), dentro do intervalo. */
function hourTicks([start, end]: [number, number], step: number): number[] {
  const hour = 3_600_000;
  const ticks: number[] = [];
  // O fuso do projeto tem deslocamento em horas cheias, então hora cheia UTC também é local.
  for (let t = Math.ceil(start / hour) * hour; t <= end; t += hour) {
    if (localHour(t) % step === 0) ticks.push(t);
  }
  return ticks;
}

interface HistoryChartProps {
  rows: ChartRow[];
  metric: Metric;
  sensors: Sensor[];
  granularity: Granularity;
  thresholds: Thresholds;
  /** Início e fim do intervalo (ms), para o eixo de tempo no modo bruto. */
  range: [number, number];
  syncId?: string;
  height?: number;
}

export function HistoryChart({ rows, metric, sensors, granularity, thresholds, range, syncId, height = 300 }: HistoryChartProps) {
  const raw = granularity === 'raw';
  const multiDay = range[1] - range[0] > 26 * 3_600_000;
  const { unit } = METRICS[metric];
  const visible = SENSORS.filter((s) => sensors.includes(s.key));
  const refs = references(metric, thresholds);
  const domain = yDomain(
    rows,
    visible.map((s) => seriesKey(s.key, metric)),
    refs.map((r) => r.value),
  );

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={rows} syncId={syncId} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="#e5e7eb" strokeDasharray="0" vertical={false} />
        {raw ? (
          <XAxis
            dataKey="x"
            type="number"
            scale="time"
            domain={range}
            ticks={hourTicks(range, multiDay ? 6 : 3)}
            tickFormatter={(x: number) => formatTick(x, multiDay)}
            tick={{ fontSize: 12, fill: '#6b7280' }}
            tickLine={false}
            axisLine={{ stroke: '#d1d5db' }}
            minTickGap={24}
          />
        ) : (
          <XAxis
            dataKey="x"
            tickFormatter={formatDay}
            tick={{ fontSize: 12, fill: '#6b7280' }}
            tickLine={false}
            axisLine={{ stroke: '#d1d5db' }}
            minTickGap={16}
          />
        )}
        <YAxis
          domain={domain}
          width={44}
          tickFormatter={(v: number) => `${v}${unit === '%' ? '%' : '°'}`}
          tick={{ fontSize: 12, fill: '#6b7280' }}
          tickLine={false}
          axisLine={false}
          allowDecimals={false}
        />
        {refs.map((r) => (
          <ReferenceLine
            key={r.label}
            y={r.value}
            stroke={r.color}
            strokeDasharray="4 4"
            strokeOpacity={0.8}
            ifOverflow="extendDomain"
            label={{ value: r.label, position: r.below ? 'insideTopRight' : 'insideBottomRight', fontSize: 11, fill: '#4b5563' }}
          />
        ))}
        <Tooltip
          content={<HistoryTooltip metric={metric} sensors={visible.map((s) => s.key)} raw={raw} />}
          cursor={{ stroke: '#9ca3af', strokeWidth: 1 }}
        />
        {!raw &&
          visible.map((s) => (
            <Area
              key={`${s.key}-range`}
              dataKey={`${seriesKey(s.key, metric)}_range`}
              name={`${s.label} mín–máx`}
              stroke="none"
              fill={s.color}
              fillOpacity={0.1}
              connectNulls={false}
              isAnimationActive={false}
              activeDot={false}
            />
          ))}
        {visible.map((s) => (
          <Line
            key={s.key}
            dataKey={seriesKey(s.key, metric)}
            name={s.label}
            stroke={s.color}
            strokeWidth={2}
            strokeDasharray={s.dash}
            dot={raw ? false : { r: 3, strokeWidth: 0, fill: s.color }}
            activeDot={{ r: 5, stroke: '#fff', strokeWidth: 2 }}
            connectNulls={false}
            isAnimationActive={false}
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
}

interface HistoryTooltipProps extends TooltipProps<number, string> {
  metric: Metric;
  sensors: Sensor[];
  raw: boolean;
}

function HistoryTooltip({ active, payload, label, metric, sensors, raw }: HistoryTooltipProps) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload as ChartRow;
  const { unit } = METRICS[metric];
  const title = raw ? formatInstant(Number(label)) : formatDay(String(label));
  const items = SENSORS.filter((s) => sensors.includes(s.key));
  const value = (key: string) => row[key] as number | null | undefined;

  return (
    <div className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs shadow-md">
      <p className="mb-1 font-medium text-gray-900">{title}</p>
      {!raw && row.samples === 0 ? (
        <p className="text-gray-500">Sem leituras neste dia</p>
      ) : (
        <ul className="space-y-1">
          {items.map((s) => {
            const key = seriesKey(s.key, metric);
            return (
              <li key={s.key} className="flex items-center gap-2 text-gray-700">
                <span className="h-0.5 w-3 shrink-0" style={{ backgroundColor: s.color }} aria-hidden />
                <span className="w-12 text-gray-500">{s.label}</span>
                {raw ? (
                  <span className="font-medium text-gray-900">{formatValue(value(key), unit)}</span>
                ) : (
                  <span>
                    máx <strong className="text-gray-900">{formatValue(value(`${key}_max`), unit)}</strong> · méd{' '}
                    <strong className="text-gray-900">{formatValue(value(key), unit)}</strong> · mín{' '}
                    <strong className="text-gray-900">{formatValue(value(`${key}_min`), unit)}</strong>
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

/** Legenda em HTML (fica acima do gráfico e funciona sem cor: o teto é tracejado). */
export function HistoryLegend({ sensors, granularity }: { sensors: Sensor[]; granularity: Granularity }) {
  return (
    <ul className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-600">
      {SENSORS.filter((s) => sensors.includes(s.key)).map((s) => (
        <li key={s.key} className="flex items-center gap-1.5">
          <svg width="20" height="8" aria-hidden>
            <line x1="0" y1="4" x2="20" y2="4" stroke={s.color} strokeWidth="2" strokeDasharray={s.dash} />
          </svg>
          {s.label}
          {granularity === 'daily' && ' (média)'}
        </li>
      ))}
      {granularity === 'daily' && (
        <li className="flex items-center gap-1.5">
          <span className="h-2.5 w-4 rounded-sm bg-gray-300/70" aria-hidden />
          Faixa entre mínima e máxima do dia
        </li>
      )}
    </ul>
  );
}
