import type { ReactNode } from 'react';

import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
}

export function EmptyState({ title, description, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white px-6 py-12 text-center">
      <div className="mb-3 text-gray-400">{icon ?? <Inbox className="h-10 w-10" aria-hidden />}</div>
      <p className="font-medium text-gray-700">{title}</p>
      {description && <p className="mt-1 max-w-md text-sm text-gray-500">{description}</p>}
    </div>
  );
}
