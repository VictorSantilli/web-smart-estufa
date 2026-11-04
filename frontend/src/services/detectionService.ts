import type { Page } from '@/types/api';
import type { Detection, DetectionQuery } from '@/types/detection';

import { api } from './api';

export async function listDetections(greenhouseId: number, query: DetectionQuery): Promise<Page<Detection>> {
  const { data } = await api.get<Page<Detection>>(`/detections/${greenhouseId}`, { params: query });
  return data;
}

/**
 * A imagem passa pelo backend (que confere o acesso à estufa) e exige o token,
 * por isso é baixada como Blob em vez de usar a URL direto no <img>.
 */
export async function getDetectionImage(
  greenhouseId: number,
  detectionId: number,
  variant: 'original' | 'heatmap' = 'original',
): Promise<Blob> {
  const { data } = await api.get<Blob>(`/detections/${greenhouseId}/${detectionId}/image`, {
    params: { variant },
    responseType: 'blob',
    timeout: 30_000,
  });
  return data;
}
