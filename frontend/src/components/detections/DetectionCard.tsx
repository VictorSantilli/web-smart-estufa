import { AlertTriangle } from 'lucide-react';

import { StatusBadge } from '@/components/ui/StatusBadge';
import type { Detection } from '@/types/detection';
import { formatDateTime } from '@/utils/datetime';

import { DetectionImage } from './DetectionImage';
import { CLASS_INFO, formatPercent } from './detectionFormat';

interface DetectionCardProps {
  detection: Detection;
  onOpen: (detection: Detection) => void;
}

export function DetectionCard({ detection, onOpen }: DetectionCardProps) {
  const info = CLASS_INFO[detection.detection_class];
  const when = formatDateTime(detection.detected_at);
  return (
    <button
      type="button"
      onClick={() => onOpen(detection)}
      className="group overflow-hidden rounded-xl border border-gray-200 bg-white text-left shadow-sm transition hover:border-brand-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-600"
      aria-label={`Detecção de ${when}: ${info.label}`}
    >
      <DetectionImage
        greenhouseId={detection.greenhouse_id}
        detectionId={detection.id}
        alt={`Foto analisada em ${when}`}
        className="aspect-[4/3] w-full"
      />
      <div className="space-y-1.5 p-3">
        <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1">
          <StatusBadge tone={info.tone}>{info.label}</StatusBadge>
          {detection.alert && (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-red-600">
              <AlertTriangle className="h-3.5 w-3.5" aria-hidden />
              Alerta
            </span>
          )}
        </div>
        <p className="text-sm text-gray-700">
          Confiança <span className="font-semibold">{formatPercent(detection.confidence)}</span>
        </p>
        <p className="text-xs text-gray-500">{when}</p>
      </div>
    </button>
  );
}
