import { formatDate, formatDateTime, formatRelative } from './datetime';

describe('datetime', () => {
  it('converte UTC para o horário de Brasília', () => {
    // 02:30 UTC = 23:30 do dia anterior em São Paulo (UTC-3)
    expect(formatDateTime('2026-11-04T02:30:00Z', 'America/Sao_Paulo')).toBe('03/11/2026, 23:30');
  });

  it('usa o dia local, não o dia UTC', () => {
    expect(formatDate('2026-11-04T01:00:00Z', 'America/Sao_Paulo')).toBe('03/11');
  });
});

describe('formatRelative', () => {
  const now = new Date('2026-11-04T12:00:00Z');
  it.each([
    ['2026-11-04T11:59:30Z', 'agora'],
    ['2026-11-04T11:55:00Z', 'há 5 min'],
    ['2026-11-04T09:00:00Z', 'há 3 h'],
    ['2026-11-01T12:00:00Z', 'há 3 dias'],
  ])('%s -> %s', (iso, expected) => {
    expect(formatRelative(iso, now)).toBe(expected);
  });
});
