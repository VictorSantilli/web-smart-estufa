import { useState, type FormEvent } from 'react';

import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { TextField } from '@/components/ui/TextField';
import { useGreenhouses } from '@/hooks/useGreenhouses';
import { useToast } from '@/hooks/useToast';
import { useCreateUser, useSaveUser } from '@/hooks/useUsers';
import { toApiError } from '@/services/api';
import type { User } from '@/types/user';

import { validateUserForm, type UserFormErrors, type UserFormValues } from './userFormValidation';

interface UserFormModalProps {
  open: boolean;
  user: User | null; // null = novo usuário
  currentUserId: number;
  onClose: () => void;
}

function initialValues(user: User | null): UserFormValues {
  return {
    name: user?.name ?? '',
    email: user?.email ?? '',
    password: '',
    isAdmin: user?.is_admin ?? false,
    greenhouseIds: user?.greenhouses.map((g) => g.id) ?? [],
  };
}

export function UserFormModal({ open, user, currentUserId, onClose }: UserFormModalProps) {
  // O componente pai usa "key" para recriar o formulário a cada abertura.
  const [values, setValues] = useState<UserFormValues>(() => initialValues(user));
  const [errors, setErrors] = useState<UserFormErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const greenhouses = useGreenhouses();
  const createUser = useCreateUser();
  const saveUser = useSaveUser();
  const toast = useToast();
  const isEdit = user !== null;
  const editingSelf = user?.id === currentUserId;
  const saving = createUser.isPending || saveUser.isPending;

  function set<K extends keyof UserFormValues>(key: K, value: UserFormValues[K]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function toggleGreenhouse(id: number) {
    set(
      'greenhouseIds',
      values.greenhouseIds.includes(id)
        ? values.greenhouseIds.filter((g) => g !== id)
        : [...values.greenhouseIds, id],
    );
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const validation = validateUserForm(values, { requirePassword: !isEdit });
    setErrors(validation);
    setFormError(null);
    if (Object.keys(validation).length > 0) return;

    try {
      if (isEdit) {
        await saveUser.mutateAsync({
          id: user.id,
          input: {
            name: values.name.trim(),
            email: values.email.trim(),
            is_admin: values.isAdmin,
            ...(values.password ? { password: values.password } : {}),
          },
          greenhouseIds: values.greenhouseIds,
        });
        toast.success('Usuário atualizado.');
      } else {
        await createUser.mutateAsync({
          name: values.name.trim(),
          email: values.email.trim(),
          password: values.password,
          is_admin: values.isAdmin,
          greenhouse_ids: values.greenhouseIds,
        });
        toast.success('Usuário cadastrado.');
      }
      onClose();
    } catch (error) {
      setFormError(toApiError(error).message);
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEdit ? 'Editar usuário' : 'Novo usuário'}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button type="submit" form="user-form" loading={saving}>
            Salvar
          </Button>
        </>
      }
    >
      <form id="user-form" onSubmit={handleSubmit} noValidate className="space-y-4">
        {formError && (
          <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {formError}
          </div>
        )}
        <TextField label="Nome" value={values.name} onChange={(e) => set('name', e.target.value)} error={errors.name} />
        <TextField
          label="E-mail"
          type="email"
          value={values.email}
          onChange={(e) => set('email', e.target.value)}
          error={errors.email}
          autoComplete="off"
        />
        <TextField
          label={isEdit ? 'Nova senha (opcional)' : 'Senha'}
          type="password"
          value={values.password}
          onChange={(e) => set('password', e.target.value)}
          error={errors.password}
          hint="Mínimo de 8 caracteres, com letras e números."
          autoComplete="new-password"
        />

        <label className="flex items-start gap-3 rounded-lg border border-gray-200 p-3">
          <input
            type="checkbox"
            className="mt-0.5 h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
            checked={values.isAdmin}
            disabled={editingSelf}
            onChange={(e) => set('isAdmin', e.target.checked)}
          />
          <span>
            <span className="block text-sm font-medium text-gray-800">Administrador</span>
            <span className="block text-xs text-gray-500">
              {editingSelf
                ? 'Você não pode remover seu próprio perfil de administrador.'
                : 'Gerencia usuários e acessa todas as estufas.'}
            </span>
          </span>
        </label>

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-gray-700">Estufas com acesso</legend>
          {values.isAdmin && (
            <p className="mb-2 text-xs text-gray-500">Administradores acessam todas as estufas.</p>
          )}
          {greenhouses.isPending && <p className="text-sm text-gray-500">Carregando estufas...</p>}
          {greenhouses.data?.length === 0 && <p className="text-sm text-gray-500">Nenhuma estufa cadastrada.</p>}
          <div className="space-y-2">
            {greenhouses.data?.map((g) => (
              <label key={g.id} className="flex items-center gap-3 text-sm text-gray-700">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                  checked={values.greenhouseIds.includes(g.id)}
                  onChange={() => toggleGreenhouse(g.id)}
                />
                {g.name ?? `Estufa ${g.id}`}
              </label>
            ))}
          </div>
        </fieldset>
      </form>
    </Modal>
  );
}
