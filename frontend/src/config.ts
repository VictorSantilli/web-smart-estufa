/** Configuração do frontend vinda de variáveis VITE_* (nunca coloque segredos aqui). */
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  timezone: import.meta.env.VITE_APP_TIMEZONE || 'America/Sao_Paulo',
  /** Deve ser igual a HISTORY_MAX_DAYS do backend (que valida de novo). */
  historyMaxDays: Number(import.meta.env.VITE_HISTORY_MAX_DAYS) || 60,
} as const;
