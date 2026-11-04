import { ImageOff } from 'lucide-react';

import { useDetectionImage } from '@/hooks/useDetections';
import { cn } from '@/utils/cn';

interface DetectionImageProps {
  greenhouseId: number;
  detectionId: number;
  alt: string;
  className?: string;
}

export function DetectionImage({ greenhouseId, detectionId, alt, className }: DetectionImageProps) {
  const { url, isError } = useDetectionImage(greenhouseId, detectionId);
  if (isError) {
    return (
      <div className={cn('flex flex-col items-center justify-center gap-1 bg-gray-100 text-xs text-gray-400', className)}>
        <ImageOff className="h-6 w-6" aria-hidden />
        Imagem indisponível
      </div>
    );
  }
  if (!url) return <div className={cn('animate-pulse bg-gray-100', className)} aria-label="Carregando imagem" />;
  return <img src={url} alt={alt} className={cn('object-cover', className)} />;
}
