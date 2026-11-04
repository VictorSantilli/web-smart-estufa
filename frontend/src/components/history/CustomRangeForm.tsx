import { type FormEvent, useState } from 'react';

import { Button } from '@/components/ui/Button';

import { addDays, todayInProjectTz, validateRange } from './chartData';

interface CustomRangeFormProps {
  initialStart?: string;
  initialEnd?: string;
  maxDays: number;
  onApply: (start: string, end: string) => void;
}

export function CustomRangeForm({ initialStart, initialEnd, maxDays, onApply }: CustomRangeFormProps) {
  const today = todayInProjectTz();
  const [start, setStart] = useState(initialStart ?? addDays(today, -13));
  const [end, setEnd] = useState(initialEnd ?? today);
  const [error, setError] = useState<string | null>(null);

  function submit(event: FormEvent) {
    event.preventDefault();
    const problem = validateRange(start, end, maxDays, today);
    setError(problem);
    if (!problem) onApply(start, end);
  }

  const input =
    'rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200';

  return (
    <form onSubmit={submit} noValidate className="flex flex-wrap items-end gap-3 rounded-lg border border-gray-200 bg-white p-3">
      <label className="flex flex-col gap-1 text-xs font-medium text-gray-600">
        De
        <input type="date" className={input} value={start} max={end || today} onChange={(e) => setStart(e.target.value)} />
      </label>
      <label className="flex flex-col gap-1 text-xs font-medium text-gray-600">
        Até
        <input type="date" className={input} value={end} min={start} max={today} onChange={(e) => setEnd(e.target.value)} />
      </label>
      <Button type="submit">Aplicar</Button>
      <p className="basis-full text-xs text-gray-500">
        Até {maxDays} dias. Períodos de até 2 dias mostram cada medição; acima disso, máxima, média e mínima por dia.
      </p>
      {error && (
        <p role="alert" className="basis-full text-sm text-red-700">
          {error}
        </p>
      )}
    </form>
  );
}
