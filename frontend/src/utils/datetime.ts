import { config } from '@/config';

/**
 * A API devolve datas em UTC (ISO 8601). A exibição é sempre no fuso do projeto,
 * independentemente do fuso do computador do usuário.
 */
export function formatDateTime(iso: string, timeZone: string = config.timezone): string {
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone,
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso));
}

export function formatDate(iso: string, timeZone: string = config.timezone): string {
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone,
    day: '2-digit',
    month: '2-digit',
  }).format(new Date(iso));
}

/** Datas sem hora (ex.: DataVinculo, "2026-11-04") são exibidas sem conversão de fuso. */
export function formatDateOnly(isoDate: string): string {
  const [year, month, day] = isoDate.split('-');
  return `${day}/${month}/${year}`;
}
