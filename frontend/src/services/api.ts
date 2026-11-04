import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

import { config } from '@/config';
import type { ApiErrorBody } from '@/types/api';
import type { TokenResponse } from '@/types/auth';

import { tokenStore } from './tokenStore';

/** Cliente HTTP único da aplicação. */
export const api = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 15_000,
  withCredentials: true, // envia o cookie HttpOnly de refresh
  headers: { 'Content-Type': 'application/json' },
});

/** Erro normalizado para a interface: sempre tem uma mensagem legível. */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number | null,
    public readonly code: string,
    public readonly fields: { field: string; message: string }[] = [],
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorBody>;
    const detail = axiosError.response?.data?.detail;
    if (detail?.message) {
      return new ApiError(
        detail.message,
        axiosError.response?.status ?? null,
        detail.code,
        detail.fields ?? [],
      );
    }
    if (!axiosError.response) {
      return new ApiError('Não foi possível conectar ao servidor.', null, 'network_error');
    }
    return new ApiError('Erro inesperado no servidor.', axiosError.response.status, 'unknown');
  }
  return new ApiError('Erro inesperado.', null, 'unknown');
}

// ---------- Sessão ----------

type SessionListener = () => void;
const sessionExpiredListeners = new Set<SessionListener>();

/** O AuthContext se registra aqui para voltar ao login quando a sessão não pode ser renovada. */
export function onSessionExpired(listener: SessionListener): () => void {
  sessionExpiredListeners.add(listener);
  return () => sessionExpiredListeners.delete(listener);
}

let refreshInFlight: Promise<string> | null = null;

/** Renova o access token. Chamadas simultâneas compartilham a mesma requisição. */
export function refreshAccessToken(): Promise<string> {
  refreshInFlight ??= api
    .post<TokenResponse>('/auth/refresh', undefined, { skipAuthRefresh: true })
    .then(({ data }) => {
      tokenStore.set(data.access_token);
      return data.access_token;
    })
    .finally(() => {
      refreshInFlight = null;
    });
  return refreshInFlight;
}

declare module 'axios' {
  interface AxiosRequestConfig {
    /** Não tenta renovar a sessão em caso de 401 (usado nas próprias rotas de auth). */
    skipAuthRefresh?: boolean;
  }
}

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

api.interceptors.request.use((request) => {
  const token = tokenStore.get();
  if (token) request.headers.Authorization = `Bearer ${token}`;
  return request;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const request = error.config as RetriableConfig | undefined;
    if (error.response?.status !== 401 || !request || request.skipAuthRefresh || request._retried) {
      return Promise.reject(error);
    }
    request._retried = true;
    try {
      const token = await refreshAccessToken();
      request.headers.Authorization = `Bearer ${token}`;
      return api(request);
    } catch {
      tokenStore.set(null);
      sessionExpiredListeners.forEach((listener) => listener());
      return Promise.reject(error);
    }
  },
);
