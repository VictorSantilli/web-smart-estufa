import type { Thresholds } from './dashboard';

export type PresetPeriod = '24h' | '7d' | '30d';
export type Granularity = 'raw' | 'daily';

export interface RawPoint {
  measured_at: string;
  device_id: string;
  canopy_temperature: number | null;
  canopy_humidity: number | null;
  ceiling_temperature: number | null;
  ceiling_humidity: number | null;
}

export interface DailyStats {
  min: number | null;
  avg: number | null;
  max: number | null;
}

export interface DailyPoint {
  date: string;
  samples: number;
  canopy_temperature: DailyStats;
  canopy_humidity: DailyStats;
  ceiling_temperature: DailyStats;
  ceiling_humidity: DailyStats;
}

export interface HistoryData {
  greenhouse_id: number;
  period: PresetPeriod | 'custom';
  granularity: Granularity;
  start: string;
  end: string;
  timezone: string;
  points: RawPoint[];
  days: DailyPoint[];
  thresholds: Thresholds;
}

/** O que o usuário escolheu: um período pronto ou um intervalo de datas (AAAA-MM-DD). */
export type HistoryQuery = { period: PresetPeriod } | { start: string; end: string };
