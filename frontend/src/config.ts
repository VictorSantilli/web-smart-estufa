/** Configuração do frontend vinda de variáveis VITE_* (nunca coloque segredos aqui). */
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  timezone: import.meta.env.VITE_APP_TIMEZONE || 'America/Sao_Paulo',
} as const;
