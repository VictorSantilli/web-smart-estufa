import { Link } from 'react-router-dom';

import { ShieldAlert } from 'lucide-react';

import { paths } from '@/routes/paths';

export function ForbiddenPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <ShieldAlert className="h-12 w-12 text-orange-500" aria-hidden />
      <p className="mt-3 text-lg font-semibold text-gray-900">Acesso restrito</p>
      <p className="mt-1 text-sm text-gray-600">Esta área é exclusiva para administradores.</p>
      <Link to={paths.dashboard} className="mt-6 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
        Voltar ao Dashboard
      </Link>
    </div>
  );
}
