import type { ReactNode } from 'react';

import { cn } from '@/utils/cn';

interface CardProps {
  title?: string;
  icon?: ReactNode;
  className?: string;
  children: ReactNode;
}

export function Card({ title, icon, className, children }: CardProps) {
  return (
    <section className={cn('rounded-xl border border-gray-200 bg-white p-5 shadow-sm', className)}>
      {title && (
        <header className="mb-3 flex items-center gap-2 text-sm font-medium text-gray-500">
          {icon}
          <h2>{title}</h2>
        </header>
      )}
      {children}
    </section>
  );
}
