export type DetectionClass = 'fungico' | 'bacteriano' | 'saudavel';

export interface Detection {
  id: number;
  greenhouse_id: number;
  /** Hora da captura (UTC). */
  detected_at: string;
  recorded_at: string | null;
  detection_class: DetectionClass;
  confidence: number;
  probabilities: {
    fungal: number | null;
    bacterial: number | null;
    healthy: number | null;
    lettuce: number | null;
  };
  pathogen_detected: boolean;
  alert: boolean;
  status: 'pending' | 'read' | 'resolved';
  has_heatmap: boolean;
  bbox: { x: number; y: number; w: number; h: number } | null;
  model_version: string;
  domain_model_version: string | null;
  inference_ms: number;
  verification_ms: number | null;
}

export interface DetectionQuery {
  class?: DetectionClass;
  start?: string;
  end?: string;
  page: number;
  page_size: number;
}
