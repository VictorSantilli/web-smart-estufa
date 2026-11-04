import { Sprout } from 'lucide-react';

import type { Greenhouse } from '@/types/greenhouse';

interface GreenhouseSelectorProps {
  greenhouses: Greenhouse[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

/** Só aparece quando o usuário tem acesso a mais de uma estufa. */
export function GreenhouseSelector({ greenhouses, selectedId, onSelect }: GreenhouseSelectorProps) {
  if (greenhouses.length <= 1) {
    const only = greenhouses[0];
    return only ? (
      <span className="inline-flex items-center gap-2 text-sm font-medium text-gray-700">
        <Sprout className="h-4 w-4 text-brand-600" aria-hidden />
        {only.name ?? `Estufa ${only.id}`}
      </span>
    ) : null;
  }
  return (
    <label className="inline-flex items-center gap-2 text-sm">
      <Sprout className="h-4 w-4 text-brand-600" aria-hidden />
      <span className="sr-only">Estufa</span>
      <select
        value={selectedId ?? ''}
        onChange={(event) => onSelect(Number(event.target.value))}
        className="rounded-lg border border-gray-300 bg-white py-1.5 pl-3 pr-8 text-sm font-medium text-gray-800 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
      >
        {greenhouses.map((g) => (
          <option key={g.id} value={g.id}>
            {g.name ?? `Estufa ${g.id}`}
          </option>
        ))}
      </select>
    </label>
  );
}
