import { Loader2 } from 'lucide-react';

import { cn } from '@/utils/cn';

export function Spinner({ className, label = 'Carregando...' }: { className?: string; label?: string }) {
  return (
    <span role="status" className={cn('inline-flex items-center gap-2 text-gray-500', className)}>
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
      <span className="text-sm">{label}</span>
    </span>
  );
}
