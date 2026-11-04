import axios, { AxiosError } from 'axios';

import { config } from '@/config';
import type { ApiErrorBody } from '@/types/api';

/** Cliente HTTP único da aplicação. Os interceptors de autenticação entram na Etapa 3. */
export const api = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 15_000,
  withCredentials: true, // envia o cookie HttpOnly de refresh (Etapa 3)
  headers: { 'Content-Type': 'application/json' },
});

/** Erro normalizado para a interface: sempre tem uma mensagem legível. */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number | null,
    public readonly code: string,
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
      return new ApiError(detail.message, axiosError.response?.status ?? null, detail.code);
    }
    if (!axiosError.response) {
      return new ApiError('Não foi possível conectar ao servidor.', null, 'network_error');
    }
    return new ApiError('Erro inesperado no servidor.', axiosError.response.status, 'unknown');
  }
  return new ApiError('Erro inesperado.', null, 'unknown');
}
