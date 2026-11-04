import { useCallback, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

import { useGreenhouses } from './useGreenhouses';

const STORAGE_KEY = 'smart-estufa:estufa';

function readStored(): number | null {
  try {
    const value = Number(localStorage.getItem(STORAGE_KEY));
    return Number.isInteger(value) && value > 0 ? value : null;
  } catch {
    return null;
  }
}

/**
 * Estufa selecionada: vem da URL (?estufa=ID), senão da última escolha do usuário,
 * senão a primeira da lista. Só aceita estufas que a API devolveu para este usuário
 * (a API valida de novo em cada consulta).
 */
export function useSelectedGreenhouse() {
  const greenhouses = useGreenhouses();
  const [params, setParams] = useSearchParams();
  const fromUrl = Number(params.get('estufa'));

  const selected = useMemo(() => {
    const list = greenhouses.data ?? [];
    const allowed = (id: number | null) => list.find((g) => g.id === id) ?? null;
    return allowed(fromUrl) ?? allowed(readStored()) ?? list[0] ?? null;
  }, [greenhouses.data, fromUrl]);

  useEffect(() => {
    if (!selected) return;
    try {
      localStorage.setItem(STORAGE_KEY, String(selected.id));
    } catch {
      /* armazenamento indisponível: segue sem lembrar a escolha */
    }
  }, [selected]);

  const select = useCallback(
    (id: number) => {
      setParams(
        (current) => {
          current.set('estufa', String(id));
          return current;
        },
        { replace: true },
      );
    },
    [setParams],
  );

  return { greenhouses, selected, select };
}
