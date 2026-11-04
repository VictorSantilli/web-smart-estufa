import { Link } from 'react-router-dom';

import { paths } from '@/routes/paths';

export function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <p className="text-5xl font-bold text-brand-600">404</p>
      <p className="mt-2 text-gray-600">Página não encontrada.</p>
      <Link to={paths.dashboard} className="mt-6 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
        Voltar ao Dashboard
      </Link>
    </div>
  );
}
