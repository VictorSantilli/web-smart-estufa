import { useState, type FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { Leaf, LogIn } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { TextField } from '@/components/ui/TextField';
import { useAuth } from '@/hooks/useAuth';
import { toApiError } from '@/services/api';
import { paths } from '@/routes/paths';
import { safeRedirectPath, validateLogin, type LoginFieldErrors } from '@/utils/validation';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<LoginFieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const errors = validateLogin(email, password);
    setFieldErrors(errors);
    setFormError(null);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      await login(email, password);
      const from = safeRedirectPath((location.state as { from?: unknown } | null)?.from, paths.dashboard);
      navigate(from === paths.login ? paths.dashboard : from, { replace: true });
    } catch (error) {
      setFormError(toApiError(error).message);
      setPassword('');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 via-white to-gray-100 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 shadow-lg">
            <Leaf className="h-8 w-8 text-white" aria-hidden />
          </span>
          <h1 className="mt-4 text-2xl font-semibold text-gray-900">Smart Estufa</h1>
          <p className="text-sm text-gray-500">Monitoramento inteligente da estufa</p>
        </div>

        <form onSubmit={handleSubmit} noValidate className="space-y-4 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          {formError && (
            <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {formError}
            </div>
          )}
          <TextField
            label="E-mail"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            error={fieldErrors.email}
            autoFocus
          />
          <TextField
            label="Senha"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            error={fieldErrors.password}
          />
          <Button type="submit" loading={submitting} className="w-full">
            {!submitting && <LogIn className="h-4 w-4" aria-hidden />}
            Entrar
          </Button>
        </form>
        <p className="mt-6 text-center text-xs text-gray-400">Acesso restrito a usuários cadastrados pelo administrador.</p>
      </div>
    </div>
  );
}
