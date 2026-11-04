import { Modal } from '@/components/ui/Modal';
import { StatusBadge } from '@/components/ui/StatusBadge';
import type { Detection } from '@/types/detection';
import { formatDateTime } from '@/utils/datetime';

import { DetectionImage } from './DetectionImage';
import { classInfo, formatPercent, probabilityRows } from './detectionFormat';

interface DetectionDetailProps {
  detection: Detection | null;
  onClose: () => void;
}

export function DetectionDetail({ detection, onClose }: DetectionDetailProps) {
  if (!detection) return null;
  const info = classInfo(detection.detection_class);
  const when = formatDateTime(detection.detected_at);
  return (
    <Modal title="Detecção da IA" open onClose={onClose}>
      <div className="space-y-4">
        <DetectionImage
          greenhouseId={detection.greenhouse_id}
          detectionId={detection.id}
          alt={`Foto analisada em ${when}`}
          className="max-h-[50vh] w-full rounded-lg object-contain"
        />
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge tone={info.tone}>{info.label}</StatusBadge>
          <span className="text-sm text-gray-700">
            Confiança <span className="font-semibold">{formatPercent(detection.confidence)}</span>
          </span>
          {detection.alert && <StatusBadge tone="critical">Alerta</StatusBadge>}
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-gray-700">Probabilidade de cada classe</p>
          <ul className="space-y-1.5">
            {probabilityRows(detection).map((row) => (
              <li key={row.label} className="grid grid-cols-[6rem_1fr_3.5rem] items-center gap-2 text-sm">
                <span className="text-gray-600">{row.label}</span>
                <span className="h-2 overflow-hidden rounded-full bg-gray-100" aria-hidden>
                  <span className="block h-full rounded-full bg-brand-600" style={{ width: `${(row.value ?? 0) * 100}%` }} />
                </span>
                <span className="text-right tabular-nums text-gray-700">{formatPercent(row.value)}</span>
              </li>
            ))}
          </ul>
        </div>

        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <dt className="text-gray-500">Capturada em</dt>
          <dd className="text-gray-800">{when}</dd>
          <dt className="text-gray-500">É alface</dt>
          <dd className="text-gray-800">{formatPercent(detection.probabilities.lettuce)}</dd>
          <dt className="text-gray-500">Modelo</dt>
          <dd className="break-all text-gray-800">{detection.model_version}</dd>
          {detection.domain_model_version && (
            <>
              <dt className="text-gray-500">Modelo de verificação</dt>
              <dd className="break-all text-gray-800">{detection.domain_model_version}</dd>
            </>
          )}
          <dt className="text-gray-500">Tempo de análise</dt>
          <dd className="text-gray-800">{Math.round(detection.inference_ms)} ms</dd>
        </dl>
      </div>
    </Modal>
  );
}
