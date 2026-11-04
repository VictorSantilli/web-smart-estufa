import { config } from '@/config';
import type { HistoryData } from '@/types/history';

export type Metric = 'temperature' | 'humidity';
export type Sensor = 'canopy' | 'ceiling';

export const SENSORS: { key: Sensor; label: string; color: string; dash?: string }[] = [
  // Paleta validada (CVD e contraste); o teto também é tracejado, para não depender só da cor.
  { key: 'canopy', label: 'Dossel', color: '#2a78d6' },
  { key: 'ceiling', label: 'Teto', color: '#1baf7a', dash: '6 4' },
];

export const METRICS: Record<Metric, { label: string; unit: string }> = {
  temperature: { label: 'Temperatura', unit: '°C' },
  humidity: { label: 'Umidade', unit: '%' },
};

/** Linha de dados do gráfico. `x` é o instante (ms) no modo bruto e a data no diário. */
export interface ChartRow {
  x: number | string;
  samples?: number;
  [key: string]: number | string | [number, number] | null | undefined;
}

export const seriesKey = (sensor: Sensor, metric: Metric) => `${sensor}_${metric}`;

/**
 * Intervalo maior que isto entre duas medições é tratado como falha de comunicação:
 * entra um ponto vazio para a linha ser interrompida em vez de ligar os dois lados.
 */
export const RAW_GAP_MS = 15 * 60_000;

export function toChartRows(data: HistoryData): ChartRow[] {
  if (data.granularity === 'raw') {
    const rows: ChartRow[] = [];
    let previous: number | null = null;
    for (const p of data.points) {
      const x = new Date(p.measured_at).getTime();
      if (previous !== null && x - previous > RAW_GAP_MS) rows.push({ x: previous + 1 });
      rows.push({
        x,
        canopy_temperature: p.canopy_temperature,
        canopy_humidity: p.canopy_humidity,
        ceiling_temperature: p.ceiling_temperature,
        ceiling_humidity: p.ceiling_humidity,
      });
      previous = x;
    }
    return rows;
  }
  return data.days.map((d) => {
    const row: ChartRow = { x: d.date, samples: d.samples };
    for (const sensor of SENSORS) {
      for (const metric of ['temperature', 'humidity'] as Metric[]) {
        const key = seriesKey(sensor.key, metric);
        const stats = d[key as keyof typeof d] as { min: number | null; avg: number | null; max: number | null };
        row[key] = stats.avg;
        row[`${key}_min`] = stats.min;
        row[`${key}_max`] = stats.max;
        row[`${key}_range`] = stats.min !== null && stats.max !== null ? [stats.min, stats.max] : null;
      }
    }
    return row;
  });
}

export function hasAnyData(data: HistoryData): boolean {
  return data.granularity === 'raw' ? data.points.length > 0 : data.days.some((d) => d.samples > 0);
}

/** Escala do eixo Y que mostra os dados e também as linhas de referência das faixas. */
export function yDomain(rows: ChartRow[], keys: string[], references: number[]): [number, number] {
  const values: number[] = [...references];
  for (const row of rows) {
    for (const key of keys) {
      for (const k of [key, `${key}_min`, `${key}_max`]) {
        const v = row[k];
        if (typeof v === 'number') values.push(v);
      }
    }
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const pad = Math.max(1, (max - min) * 0.08);
  return [Math.floor(min - pad), Math.ceil(max + pad)];
}

// ---------- datas no fuso do projeto ----------

const fmt = (options: Intl.DateTimeFormatOptions) =>
  new Intl.DateTimeFormat('pt-BR', { timeZone: config.timezone, ...options });
const timeFmt = fmt({ hour: '2-digit', minute: '2-digit' });
const dayTimeFmt = fmt({ day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });

export const formatTick = (x: number, multiDay: boolean) =>
  multiDay ? dayTimeFmt.format(x) : timeFmt.format(x);
export const formatInstant = (x: number) => dayTimeFmt.format(x);
const hourFmt = fmt({ hour: 'numeric', hourCycle: 'h23' });
export const localHour = (x: number) => Number(hourFmt.format(x));

/** "2026-11-04" → "04/11" (data local vinda da API, sem conversão de fuso). */
export const formatDay = (isoDate: string) => `${isoDate.slice(8, 10)}/${isoDate.slice(5, 7)}`;

/** Data de hoje no fuso do projeto, no formato AAAA-MM-DD. */
export function todayInProjectTz(now: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: config.timezone }).format(now);
}

export function addDays(isoDate: string, days: number): string {
  const d = new Date(`${isoDate}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export function daysBetweenInclusive(start: string, end: string): number {
  return Math.round((Date.parse(end) - Date.parse(start)) / 86_400_000) + 1;
}

export const formatValue = (v: number | null | undefined, unit: string) =>
  v === null || v === undefined ? '—' : `${v.toLocaleString('pt-BR', { maximumFractionDigits: 1 })} ${unit}`.trim();

export function validateRange(start: string, end: string, maxDays: number, today: string): string | null {
  if (!start || !end) return 'Informe a data inicial e a data final.';
  if (start > end) return 'A data inicial deve ser anterior à data final.';
  if (end > today) return 'A data final não pode estar no futuro.';
  if (daysBetweenInclusive(start, end) > maxDays) return `O período pode ter no máximo ${maxDays} dias.`;
  return null;
}
