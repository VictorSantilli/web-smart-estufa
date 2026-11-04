import { AxiosError, AxiosHeaders } from 'axios';

import { ApiError, toApiError } from './api';

function axiosErrorWith(status: number | null, data?: unknown) {
  const config = { headers: new AxiosHeaders() };
  const response =
    status === null ? undefined : { status, statusText: '', headers: {}, config, data };
  return new AxiosError('fail', 'ERR', config, null, response);
}

describe('toApiError', () => {
  it('usa a mensagem padronizada do backend', () => {
    const err = toApiError(
      axiosErrorWith(422, { detail: { code: 'validation_error', message: 'Dados inválidos.' } }),
    );
    expect(err).toBeInstanceOf(ApiError);
    expect(err.message).toBe('Dados inválidos.');
    expect(err.status).toBe(422);
    expect(err.code).toBe('validation_error');
  });

  it('identifica falha de rede', () => {
    expect(toApiError(axiosErrorWith(null)).code).toBe('network_error');
  });
});
