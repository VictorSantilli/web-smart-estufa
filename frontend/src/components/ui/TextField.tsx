import { forwardRef, useId, type InputHTMLAttributes } from 'react';

import { cn } from '@/utils/cn';

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, error, hint, className, id, ...props },
  ref,
) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const messageId = `${inputId}-message`;
  return (
    <div className={className}>
      <label htmlFor={inputId} className="mb-1 block text-sm font-medium text-gray-700">
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        aria-invalid={Boolean(error)}
        aria-describedby={error || hint ? messageId : undefined}
        className={cn(
          'block w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none transition-colors',
          'focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20',
          error ? 'border-red-400' : 'border-gray-300',
        )}
        {...props}
      />
      {(error || hint) && (
        <p id={messageId} className={cn('mt-1 text-xs', error ? 'text-red-600' : 'text-gray-500')}>
          {error ?? hint}
        </p>
      )}
    </div>
  );
});
