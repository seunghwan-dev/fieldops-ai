export interface IngestResponse {
  doc_id: string;
  doc_title: string;
  pages_processed: number;
  chunks_created: number;
  chunk_distribution: {
    text: number;
    table_row: number;
    figure: number;
  };
  tables: Array<{
    table_id: string;
    caption: string;
    headers: string[];
    row_count: number;
  }>;
  figures: Array<{
    figure_id: string;
    type: string;
    semantic_summary: string;
  }>;
  status: 'new' | 'updated' | 'unchanged';
  file_hash: string; // SHA-256 hex digest (64 chars)
}

export interface SearchResult {
  chunk_id: string;
  chunk_type: string;
  chunk_text: string;
  doc_id: string;
  doc_title: string;
  page_number: number;
  similarity: number;
  search_method: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  answer: string;
  sources: string[];
  total_results: number;
  search_meta: {
    vector_hits: number;
    bm25_hits: number;
    search_time_ms: number;
  };
}

// ===== Fusion (Phase 4 API) =====
// Equipment A conditions: temperature_celsius, rpm, fill_ratio_percent,
//   blade_type (A~G), machine_prop_a, machine_prop_b, machine_prop_c
// Equipment B conditions: feed_rate_kg_h, grinding_pressure_mpa,
//   classifier_rpm, air_flow
export interface ShapFactor {
  feature: string;
  value: number;
  shap_value: number;
  direction: string;
}

export interface FusionResponse {
  mode: 'ml_only' | 'fusion';
  prediction: {
    discharge_temp_celsius: number | null;
    d50_micron: number | null;
    physics_only_d50?: number;
    ml_correction?: number;
    confidence: number;
    model: string;
    physics_formula?: string;
  };
  shap: {
    top_factors: ShapFactor[];
    base_value: number;
    explanation: string;
  };
  domain_knowledge: {
    rag_hits: number;
    top_results: Array<{
      source: string;
      page: number;
      similarity: number;
      text: string;
    }>;
  } | null;
  fusion: {
    fused_prediction: number;
    correction_applied: boolean;
    correction_delta: number;
    correction_reason: string;
    domain_evidence: string[];
    risk_level: string;
    recommendation: string;
    confidence_score: number;
    fusion_method: string;
  } | null;
  safety_overrides: Array<{
    rule_id: string;
    severity: string;
    message: string;
  }>;
  requires_human_review: boolean;
  meta: {
    total_time_ms: number;
  };
}
