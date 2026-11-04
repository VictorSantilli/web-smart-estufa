import { ShieldCheck } from 'lucide-react';

import { EmptyState } from '@/components/ui/EmptyState';

export function AdminPlaceholderPage({ title }: { title: string }) {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">{title}</h1>
      <EmptyState
        icon={<ShieldCheck className="h-10 w-10" aria-hidden />}
        title="Área do administrador"
        description="O gerenciamento de usuários e de acessos às estufas chega na Etapa 3."
      />
    </div>
  );
}
