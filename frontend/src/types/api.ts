/** Formato padrão de erro devolvido pelo backend. */
export interface ApiErrorBody {
  detail: {
    code: string;
    message: string;
    fields?: { field: string; message: string }[];
  };
}

export interface HealthResponse {
  status: 'ok' | 'degraded';
  database: 'ok' | 'unavailable';
  version: string;
  environment: string;
}
