import { LineChart } from 'lucide-react';

import { EmptyState } from '@/components/ui/EmptyState';

export function HistoryPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Histórico</h1>
        <p className="text-sm text-gray-500">Evolução da temperatura e da umidade.</p>
      </div>
      <EmptyState
        icon={<LineChart className="h-10 w-10" aria-hidden />}
        title="Gráficos em construção"
        description="Os filtros de 24 horas, 7 dias e 30 dias e os gráficos de máxima, média e mínima chegam na Etapa 5."
      />
    </div>
  );
}
