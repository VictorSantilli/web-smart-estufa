import { useCallback, useMemo, useState, type ReactNode } from 'react';

import { CheckCircle2, X, XCircle } from 'lucide-react';

import { cn } from '@/utils/cn';

import { ToastContext } from './toastContextValue';

type ToastTone = 'success' | 'error';
interface Toast {
  id: number;
  tone: ToastTone;
  message: string;
}

let nextId = 1;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (tone: ToastTone, message: string) => {
      const id = nextId++;
      setToasts((current) => [...current, { id, tone, message }]);
      setTimeout(() => dismiss(id), 4000);
    },
    [dismiss],
  );

  const value = useMemo(
    () => ({
      success: (message: string) => push('success', message),
      error: (message: string) => push('error', message),
    }),
    [push],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed inset-x-4 bottom-4 z-50 flex flex-col items-end gap-2 sm:inset-x-auto sm:right-6">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role={toast.tone === 'error' ? 'alert' : 'status'}
            className={cn(
              'pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-lg border bg-white p-4 shadow-lg',
              toast.tone === 'success' ? 'border-green-200' : 'border-red-200',
            )}
          >
            {toast.tone === 'success' ? (
              <CheckCircle2 className="h-5 w-5 shrink-0 text-green-600" aria-hidden />
            ) : (
              <XCircle className="h-5 w-5 shrink-0 text-red-600" aria-hidden />
            )}
            <p className="flex-1 text-sm text-gray-700">{toast.message}</p>
            <button onClick={() => dismiss(toast.id)} aria-label="Fechar" className="text-gray-400 hover:text-gray-600">
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
