import { formatDate, formatDateTime } from './datetime';

describe('datetime', () => {
  it('converte UTC para o horário de Brasília', () => {
    // 02:30 UTC = 23:30 do dia anterior em São Paulo (UTC-3)
    expect(formatDateTime('2026-11-04T02:30:00Z', 'America/Sao_Paulo')).toBe('03/11/2026, 23:30');
  });

  it('usa o dia local, não o dia UTC', () => {
    expect(formatDate('2026-11-04T01:00:00Z', 'America/Sao_Paulo')).toBe('03/11');
  });
});
