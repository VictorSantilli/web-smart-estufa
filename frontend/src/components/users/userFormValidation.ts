export interface UserFormValues {
  name: string;
  email: string;
  password: string;
  isAdmin: boolean;
  greenhouseIds: number[];
}

export type UserFormErrors = Partial<Record<'name' | 'email' | 'password', string>>;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Mesmas regras do backend (que valida de novo). */
export function validateUserForm(values: UserFormValues, options: { requirePassword: boolean }): UserFormErrors {
  const errors: UserFormErrors = {};
  if (values.name.trim().length < 2) errors.name = 'Informe o nome (mínimo de 2 caracteres).';
  if (!EMAIL_PATTERN.test(values.email.trim())) errors.email = 'E-mail inválido.';
  const { password } = values;
  if (password || options.requirePassword) {
    if (password.length < 8 || password.length > 128 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
      errors.password = 'A senha deve ter de 8 a 128 caracteres, com letras e números.';
    }
  }
  return errors;
}
