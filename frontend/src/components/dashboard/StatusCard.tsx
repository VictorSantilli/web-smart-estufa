import type { ReactNode } from 'react';

import { cn } from '@/utils/cn';

type Tone = 'ok' | 'warning' | 'critical' | 'neutral';

const tones: Record<Tone, { icon: string; text: string }> = {
  ok: { icon: 'bg-green-100 text-green-700', text: 'text-green-700' },
  warning: { icon: 'bg-orange-100 text-orange-700', text: 'text-orange-700' },
  critical: { icon: 'bg-red-100 text-red-700', text: 'text-red-700' },
  neutral: { icon: 'bg-gray-100 text-gray-500', text: 'text-gray-600' },
};

interface StatusCardProps {
  title: string;
  icon: ReactNode;
  tone: Tone;
  status: string;
  children?: ReactNode;
}

export function StatusCard({ title, icon, tone, status, children }: StatusCardProps) {
  return (
    <section aria-label={title} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <span className={cn('flex h-10 w-10 shrink-0 items-center justify-center rounded-lg', tones[tone].icon)}>
          {icon}
        </span>
        <div className="min-w-0">
          <p className="text-sm text-gray-500">{title}</p>
          <p className={cn('truncate text-lg font-semibold', tones[tone].text)}>{status}</p>
        </div>
      </div>
      {children && <div className="mt-3 space-y-1 text-xs text-gray-500">{children}</div>}
    </section>
  );
}
