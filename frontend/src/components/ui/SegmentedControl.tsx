import { cn } from '@/utils/cn';

interface SegmentedControlProps<T extends string> {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}

/** Grupo de botões de escolha única (acessível como radiogroup). */
export function SegmentedControl<T extends string>({ label, value, options, onChange }: SegmentedControlProps<T>) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex max-w-full overflow-x-auto rounded-lg border border-gray-200 bg-white p-0.5">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={value === option.value}
          onClick={() => onChange(option.value)}
          className={cn(
            'whitespace-nowrap rounded-md px-3 py-1 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-600',
            value === option.value ? 'bg-brand-600 text-white' : 'text-gray-600 hover:bg-gray-100',
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
