import type { Page } from '@/types/api';
import type { User, UserCreateInput, UserUpdateInput } from '@/types/user';

import { api } from './api';

export interface UserListParams {
  q?: string;
  active?: boolean;
  page: number;
  page_size: number;
}

export async function listUsers(params: UserListParams): Promise<Page<User>> {
  const { data } = await api.get<Page<User>>('/users', { params });
  return data;
}

export async function createUser(input: UserCreateInput): Promise<User> {
  const { data } = await api.post<User>('/users', input);
  return data;
}

export async function updateUser(id: number, input: UserUpdateInput): Promise<User> {
  const { data } = await api.patch<User>(`/users/${id}`, input);
  return data;
}

export async function setUserActive(id: number, active: boolean): Promise<User> {
  const { data } = await api.post<User>(`/users/${id}/${active ? 'activate' : 'deactivate'}`);
  return data;
}

export async function setUserGreenhouses(id: number, greenhouseIds: number[]): Promise<User> {
  const { data } = await api.put<User>(`/users/${id}/greenhouses`, {
    greenhouse_ids: greenhouseIds,
  });
  return data;
}
