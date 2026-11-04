import { validateUserForm } from '@/components/users/userFormValidation';

import { validateLogin } from './validation';

describe('validateLogin', () => {
  it('exige e-mail e senha', () => {
    expect(validateLogin('', '')).toEqual({ email: 'Informe o e-mail.', password: 'Informe a senha.' });
  });

  it('rejeita e-mail mal formatado', () => {
    expect(validateLogin('ana@', 'x').email).toBe('E-mail inválido.');
  });

  it('aceita dados válidos', () => {
    expect(validateLogin(' ana@estufa.com ', 'x')).toEqual({});
  });
});

describe('validateUserForm', () => {
  const base = { name: 'Ana', email: 'ana@estufa.com', password: 'Senha123', isAdmin: false, greenhouseIds: [] };

  it('aceita usuário válido', () => {
    expect(validateUserForm(base, { requirePassword: true })).toEqual({});
  });

  it.each(['curta1', 'semnumero', '12345678'])('rejeita senha fraca: %s', (password) => {
    expect(validateUserForm({ ...base, password }, { requirePassword: true }).password).toBeDefined();
  });

  it('senha é opcional na edição', () => {
    expect(validateUserForm({ ...base, password: '' }, { requirePassword: false })).toEqual({});
  });
});
