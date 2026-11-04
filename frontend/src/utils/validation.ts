export const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export interface LoginFieldErrors {
  email?: string;
  password?: string;
}

export function validateLogin(email: string, password: string): LoginFieldErrors {
  const errors: LoginFieldErrors = {};
  if (!email.trim()) errors.email = 'Informe o e-mail.';
  else if (!EMAIL_PATTERN.test(email.trim())) errors.email = 'E-mail inválido.';
  if (!password) errors.password = 'Informe a senha.';
  return errors;
}

/**
 * Caminho interno seguro para voltar depois do login. Recusa URLs absolutas e caminhos
 * como "//site.com" ou "/\site.com", que o navegador trataria como outro domínio
 * (proteção contra redirecionamento aberto).
 */
export function safeRedirectPath(from: unknown, fallback: string): string {
  if (typeof from !== 'string' || !from.startsWith('/')) return fallback;
  if (from.startsWith('//') || from.includes('\\') || [...from].some((c) => c.charCodeAt(0) < 32)) return fallback;
  return from;
}
