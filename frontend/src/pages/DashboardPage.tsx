import { Droplets, Fan, Thermometer, Wifi } from 'lucide-react';

import { ApiStatus } from '@/components/ApiStatus';
import { Card } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500">Situação atual da estufa.</p>
      </div>

      <div className="sm:hidden">
        <ApiStatus />
      </div>

      {/* Estrutura dos cards; os dados reais entram na Etapa 4 */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card title="Temperatura" icon={<Thermometer className="h-4 w-4" />}>
          <p className="text-3xl font-semibold text-gray-300">-- °C</p>
        </Card>
        <Card title="Umidade" icon={<Droplets className="h-4 w-4" />}>
          <p className="text-3xl font-semibold text-gray-300">-- %</p>
        </Card>
        <Card title="Comunicação" icon={<Wifi className="h-4 w-4" />}>
          <p className="text-sm text-gray-400">Sem dados</p>
        </Card>
        <Card title="Ventoinhas" icon={<Fan className="h-4 w-4" />}>
          <p className="text-sm text-gray-400">Sem informação</p>
        </Card>
      </div>

      <EmptyState
        title="Indicadores em construção"
        description="Os dados de temperatura, umidade e status dos sensores serão exibidos aqui na Etapa 4."
      />
    </div>
  );
}
