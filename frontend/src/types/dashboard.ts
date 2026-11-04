import type { Greenhouse } from './greenhouse';

export type Level = 'low' | 'ok' | 'warning' | 'critical';

export interface Measurement {
  value: number | null;
  level: Level | null;
  measured_at: string | null;
  is_current: boolean;
}

export interface SensorStatus {
  ok: boolean;
  temperature: Measurement;
  humidity: Measurement;
}

export interface Thresholds {
  temp_min: number;
  temp_warning: number;
  temp_critical: number;
  humidity_min: number;
  humidity_max: number;
}

export interface DashboardData {
  greenhouse: Greenhouse;
  has_data: boolean;
  last_reading_at: string | null;
  last_communication_at: string | null;
  is_online: boolean;
  stale_after_minutes: number;
  canopy: SensorStatus;
  ceiling: SensorStatus;
  fans: { state: 'on' | 'off' | 'unknown'; measured_at: string | null };
  thresholds: Thresholds;
  generated_at: string;
}
