import type { CurrentUser, TokenResponse } from '@/types/auth';

import { api } from './api';
import { tokenStore } from './tokenStore';

export async function login(email: string, password: string): Promise<void> {
  const { data } = await api.post<TokenResponse>(
    '/auth/login',
    { email: email.trim(), password },
    { skipAuthRefresh: true },
  );
  tokenStore.set(data.access_token);
}

export async function getMe(): Promise<CurrentUser> {
  const { data } = await api.get<CurrentUser>('/auth/me');
  return data;
}

export async function logout(): Promise<void> {
  try {
    await api.post('/auth/logout', undefined, { skipAuthRefresh: true });
  } finally {
    tokenStore.set(null);
  }
}
