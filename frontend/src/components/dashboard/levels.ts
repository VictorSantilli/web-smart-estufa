import type { Level, Thresholds } from '@/types/dashboard';

/** Cores e textos de cada faixa. Cor nunca é o único sinal: sempre há um rótulo. */
export const levelStyles: Record<Level, { card: string; value: string; badge: string; label: string }> = {
  low: {
    card: 'border-blue-200 bg-blue-50/60',
    value: 'text-blue-700',
    badge: 'bg-blue-100 text-blue-800',
    label: 'Abaixo do ideal',
  },
  ok: {
    card: 'border-gray-200 bg-white',
    value: 'text-gray-900',
    badge: 'bg-green-100 text-green-800',
    label: 'Normal',
  },
  warning: {
    card: 'border-orange-300 bg-orange-50/70',
    value: 'text-orange-700',
    badge: 'bg-orange-100 text-orange-800',
    label: 'Atenção',
  },
  critical: {
    card: 'border-red-300 bg-red-50/70',
    value: 'text-red-700',
    badge: 'bg-red-100 text-red-800',
    label: 'Crítico',
  },
};

export function levelLabel(level: Level, kind: 'temperature' | 'humidity'): string {
  if (kind === 'humidity' && level === 'warning') return 'Risco de fungos';
  if (kind === 'temperature' && level === 'warning') return 'Acima do ideal';
  return levelStyles[level].label;
}

export function rangeHint(kind: 'temperature' | 'humidity', t: Thresholds): string {
  return kind === 'temperature'
    ? `Ideal ${t.temp_min}–${t.temp_warning} °C`
    : `Ideal ${t.humidity_min}–${t.humidity_max} %`;
}
