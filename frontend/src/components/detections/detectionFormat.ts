import type { StatusTone } from '@/components/ui/StatusBadge';
import type { Detection, DetectionClass } from '@/types/detection';

export const CLASS_INFO: Record<DetectionClass, { label: string; tone: StatusTone }> = {
  saudavel: { label: 'Saudável', tone: 'ok' },
  fungico: { label: 'Fúngico', tone: 'warning' },
  bacteriano: { label: 'Bacteriano', tone: 'critical' },
  nao_alface: { label: 'Não é alface', tone: 'neutral' },
};

const NOT_LETTUCE = new Set(['nao-alface', 'naoalface', 'nao_e_alface', 'outro', 'desconhecido']);

/** Rótulo e cor do resultado; valores fora das três classes não quebram a tela. */
export function classInfo(value: string): { label: string; tone: StatusTone } {
  const key = value.trim().toLowerCase();
  if (key in CLASS_INFO) return CLASS_INFO[key as DetectionClass];
  if (NOT_LETTUCE.has(key)) return { label: 'Não é alface', tone: 'neutral' };
  const label = key.replace(/[_-]+/g, ' ').trim();
  return { label: label ? label.charAt(0).toUpperCase() + label.slice(1) : 'Sem resultado', tone: 'neutral' };
}

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
