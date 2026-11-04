import { cn } from '@/utils/cn';

export type StatusTone = 'ok' | 'warning' | 'critical' | 'cold' | 'neutral';

const tones: Record<StatusTone, string> = {
  ok: 'bg-green-50 text-green-700 ring-green-600/20',
  warning: 'bg-orange-50 text-orange-700 ring-orange-600/20',
  critical: 'bg-red-50 text-red-700 ring-red-600/20',
  cold: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  neutral: 'bg-gray-100 text-gray-600 ring-gray-500/20',
};

export function StatusBadge({ tone, children }: { tone: StatusTone; children: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
        tones[tone],
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden />
      {children}
    </span>
  );
}
