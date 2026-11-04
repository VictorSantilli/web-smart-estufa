import type { StatusTone } from '@/components/ui/StatusBadge';
import type { Detection, DetectionClass } from '@/types/detection';

export const CLASS_INFO: Record<DetectionClass, { label: string; tone: StatusTone }> = {
  saudavel: { label: 'Saudável', tone: 'ok' },
  fungico: { label: 'Fúngico', tone: 'warning' },
  bacteriano: { label: 'Bacteriano', tone: 'critical' },
};

export function formatPercent(value: number | null): string {
  if (value === null) return '—';
  return `${(value * 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`;
}

export function probabilityRows(detection: Detection): { label: string; value: number | null }[] {
  const p = detection.probabilities;
  return [
    { label: 'Saudável', value: p.healthy },
    { label: 'Fúngico', value: p.fungal },
    { label: 'Bacteriano', value: p.bacterial },
  ];
}
