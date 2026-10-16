export const CATEGORIES = {
  status_pengiriman: "Status pengiriman",
  barang_rusak: "Barang rusak",
  barang_tidak_sesuai: "Barang tidak sesuai",
  retur_refund: "Retur & refund",
  pembatalan: "Pembatalan",
  pembayaran: "Pembayaran",
  akun: "Akun",
  lainnya: "Lainnya",
} as const;
export const TEAMS = {
  logistik: "Logistik",
  retur: "Retur",
  billing: "Billing",
  customer_care: "Customer care",
} as const;
export const STATUSES = {
  baru: "Baru",
  ditinjau: "Perlu ditinjau",
  disetujui: "Disetujui",
  selesai: "Selesai",
} as const;
export type Category = keyof typeof CATEGORIES;
export type Status = keyof typeof STATUSES;
export interface Policy {
  id: string;
  title: string;
  body: string;
  category?: Category;
  version: number;
}
export interface Draft {
  id: string;
  ticket_id: string;
  revision: number;
  body: string;
  source: string;
  policy_refs: Policy[];
  missing_information: string[];
  review_flags: string[];
  status: string;
  version: number;
  model_version: string;
  created_at: string;
}
export interface Job {
  id: string;
  status: string;
  stage: string;
  error: string | null;
  revision: number;
}
export interface Analysis {
  category: Category;
  score: number | null;
  calibration: string;
  needs_review: boolean;
  classifier_version: string;
  source: string;
  top_classes?: { category: Category; score: number }[];
  priority_reason?: string;
}
export interface Ticket {
  id: string;
  number: number;
  subject: string;
  message: string;
  customer: string;
  order_code: string | null;
  status: Status;
  category: Category | null;
  team: keyof typeof TEAMS;
  priority: string;
  revision: number;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  analysis: Analysis | null;
  analysis_revision: number | null;
  job: Job | null;
  drafts?: Draft[];
  events?: {
    id: string;
    action: string;
    created_at: string;
    detail: Record<string, unknown>;
  }[];
  order?: Record<string, unknown> | null;
}
export interface Overview {
  total: number;
  new: number;
  review: number;
  resolved: number;
  approved: number;
  corrections: number;
  categories: Record<string, number>;
  daily: { date: string; count: number }[];
}
export interface Evaluation {
  id: string;
  model: string;
  dataset_version: string;
  synthetic: boolean;
  reviewed_by_human: boolean;
  test_count: number;
  macro_f1: number;
  accuracy: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  labels: Category[];
  confusion_matrix: number[][];
  per_class: Record<
    string,
    { precision: number; recall: number; "f1-score": number; support: number }
  >;
  errors: { text: string; expected: Category; predicted: Category }[];
  created_at: string;
  notes: string[];
}
export interface Readiness {
  api: string;
  database: string;
  classifier: {
    version: string;
    type: string;
    calibration?: string;
    review_required?: boolean;
  };
  ollama: boolean;
  llm_model: string;
  queue: number;
  mode: string;
  version: string;
}
