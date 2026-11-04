import type { HistoryData } from '@/types/history';

import { addDays, daysBetweenInclusive, localHour, RAW_GAP_MS, toChartRows, todayInProjectTz, validateRange, yDomain } from './chartData';

const thresholds = { temp_min: 16, temp_warning: 25, temp_critical: 26, humidity_min: 65, humidity_max: 85 };
const stats = (min: number | null, avg: number | null, max: number | null) => ({ min, avg, max });

function base(overrides: Partial<HistoryData>): HistoryData {
  return {
    greenhouse_id: 1,
    period: '24h',
    granularity: 'raw',
    start: '2026-03-14T12:00:00Z',
    end: '2026-03-15T12:00:00Z',
    timezone: 'America/Sao_Paulo',
    points: [],
    days: [],
    thresholds,
    ...overrides,
  };
}

const point = (iso: string, t: number | null) => ({
  measured_at: iso,
  device_id: 'esp32-01',
  canopy_temperature: t,
  canopy_humidity: 70,
  ceiling_temperature: 24,
  ceiling_humidity: 72,
});

describe('toChartRows', () => {
  it('interrompe a linha quando falta comunicação', () => {
    const rows = toChartRows(
      base({ points: [point('2026-03-15T10:00:00Z', 20), point('2026-03-15T10:05:00Z', 21), point('2026-03-15T11:00:00Z', 22)] }),
    );
    expect(rows).toHaveLength(4);
    expect(rows[2].canopy_temperature).toBeUndefined();
    expect(Number(rows[3].x) - Number(rows[1].x)).toBeGreaterThan(RAW_GAP_MS);
  });

  it('monta média e faixa mín–máx por dia, com dias vazios', () => {
    const empty = stats(null, null, null);
    const rows = toChartRows(
      base({
        granularity: 'daily',
        period: '7d',
        days: [
          { date: '2026-03-14', samples: 3, canopy_temperature: stats(18, 20, 22), canopy_humidity: stats(70, 80, 90), ceiling_temperature: empty, ceiling_humidity: empty },
          { date: '2026-03-15', samples: 0, canopy_temperature: empty, canopy_humidity: empty, ceiling_temperature: empty, ceiling_humidity: empty },
        ],
      }),
    );
    expect(rows[0]).toMatchObject({ x: '2026-03-14', canopy_temperature: 20, canopy_temperature_range: [18, 22] });
    expect(rows[0].ceiling_temperature_range).toBeNull();
    expect(rows[1]).toMatchObject({ samples: 0, canopy_temperature: null, canopy_temperature_range: null });
  });
});

describe('yDomain', () => {
  it('inclui os valores e as linhas de referência', () => {
    const [min, max] = yDomain([{ x: 1, a: 20, a_max: 30 }], ['a'], [16, 26]);
    expect(min).toBeLessThan(16);
    expect(max).toBeGreaterThan(30);
  });
});

describe('datas', () => {
  it('calcula hoje no fuso do projeto', () => {
    // 02:00 UTC ainda é o dia anterior em Brasília
    expect(todayInProjectTz(new Date('2026-03-10T02:00:00Z'))).toBe('2026-03-09');
  });

  it('soma e conta dias', () => {
    expect(addDays('2026-02-27', 2)).toBe('2026-03-01');
    expect(daysBetweenInclusive('2026-01-15', '2026-03-15')).toBe(60);
  });

  it('valida o período personalizado', () => {
    const today = '2026-03-15';
    expect(validateRange('2026-01-15', '2026-03-15', 60, today)).toBeNull();
    expect(validateRange('2026-01-14', '2026-03-15', 60, today)).toMatch('60 dias');
    expect(validateRange('2026-03-10', '2026-03-09', 60, today)).toMatch('anterior');
    expect(validateRange('2026-03-10', '2026-03-16', 60, today)).toMatch('futuro');
    expect(validateRange('', '2026-03-10', 60, today)).toMatch('Informe');
  });
});

describe('localHour', () => {
  it('usa o fuso do projeto', () => {
    expect(localHour(Date.parse('2026-03-10T03:00:00Z'))).toBe(0);
  });
});
