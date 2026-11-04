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
