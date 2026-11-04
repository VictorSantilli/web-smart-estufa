import type { HistoryData } from '@/types/history';

import { formatDay, formatInstant, formatValue, METRICS, type Metric, type Sensor, SENSORS, seriesKey } from './chartData';

interface HistoryTableProps {
  data: HistoryData;
  metrics: Metric[];
  sensors: Sensor[];
}

/** Os mesmos dados do gráfico em tabela (mais recentes primeiro). */
export function HistoryTable({ data, metrics, sensors }: HistoryTableProps) {
  const columns = metrics.flatMap((metric) =>
    SENSORS.filter((s) => sensors.includes(s.key)).map((s) => ({
      key: seriesKey(s.key, metric),
      label: `${METRICS[metric].label} ${s.label.toLowerCase()}`,
      unit: METRICS[metric].unit,
    })),
  );
  const raw = data.granularity === 'raw';

  return (
    <div className="max-h-[28rem] overflow-auto rounded-lg border border-gray-200">
      <table className="min-w-full text-sm">
        <thead className="sticky top-0 bg-gray-50 text-left text-xs font-medium text-gray-500">
          <tr>
            <th scope="col" className="whitespace-nowrap px-3 py-2">
              {raw ? 'Medição' : 'Dia'}
            </th>
            {columns.map((c) => (
              <th key={c.key} scope="col" className="whitespace-nowrap px-3 py-2">
                {c.label}
                {!raw && <span className="block font-normal text-gray-400">mín · méd · máx</span>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 text-gray-700">
          {raw
            ? [...data.points].reverse().map((p) => (
                <tr key={`${p.device_id}-${p.measured_at}`}>
                  <td className="whitespace-nowrap px-3 py-1.5 text-gray-500">{formatInstant(new Date(p.measured_at).getTime())}</td>
                  {columns.map((c) => (
                    <td key={c.key} className="whitespace-nowrap px-3 py-1.5 tabular-nums">
                      {formatValue(p[c.key as keyof typeof p] as number | null, c.unit)}
                    </td>
                  ))}
                </tr>
              ))
            : [...data.days].reverse().map((d) => (
                <tr key={d.date}>
                  <td className="whitespace-nowrap px-3 py-1.5 text-gray-500">{formatDay(d.date)}</td>
                  {columns.map((c) => {
                    const s = d[c.key as keyof typeof d] as { min: number | null; avg: number | null; max: number | null };
                    return (
                      <td key={c.key} className="whitespace-nowrap px-3 py-1.5 tabular-nums">
                        {d.samples === 0
                          ? 'sem dados'
                          : `${formatValue(s.min, '')} · ${formatValue(s.avg, '')} · ${formatValue(s.max, c.unit)}`}
                      </td>
                    );
                  })}
                </tr>
              ))}
        </tbody>
      </table>
    </div>
  );
}
