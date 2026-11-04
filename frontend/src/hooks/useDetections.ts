import { useEffect, useState } from 'react';

import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { getDetectionImage, listDetections } from '@/services/detectionService';
import type { DetectionQuery } from '@/types/detection';

export function useDetections(greenhouseId: number | null, query: DetectionQuery) {
  return useQuery({
    queryKey: ['detections', greenhouseId, query],
    queryFn: () => listDetections(greenhouseId!, query),
    enabled: greenhouseId !== null,
    placeholderData: keepPreviousData,
    refetchInterval: 120_000,
    staleTime: 30_000,
  });
}

/** Baixa a imagem da detecção e devolve uma URL local (blob:) para o <img>. */
export function useDetectionImage(greenhouseId: number, detectionId: number, variant: 'original' | 'heatmap' = 'original') {
  const image = useQuery({
    queryKey: ['detection-image', greenhouseId, detectionId, variant],
    queryFn: () => getDetectionImage(greenhouseId, detectionId, variant),
    // A imagem de uma detecção não muda.
    staleTime: Infinity,
    gcTime: 10 * 60_000,
    retry: 1,
  });
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!image.data) return;
    const objectUrl = URL.createObjectURL(image.data);
    setUrl(objectUrl);
    return () => {
      URL.revokeObjectURL(objectUrl);
      setUrl(null);
    };
  }, [image.data]);

  return { url, isError: image.isError, isPending: image.isPending };
}
