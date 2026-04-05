// WHY: Realistic mock data for DEMO mode when Docker backend is unavailable.
// INTERVIEW: "Graceful degradation — demo works without infrastructure."

import type { IngestResponse, SearchResponse, FusionResponse } from '../types/api';

// ===== Knowledge Ingest — 3 sample documents =====

export const mockIngestResponse: IngestResponse = {
  doc_id: 'paper-a-material-x-thermal-stability',
  doc_title: 'Thermal Stability Analysis of Material X in High-Shear Mixing Processes',
  pages_processed: 4,
  chunks_created: 19,
  chunk_distribution: { text: 9, table_row: 8, figure: 2 },
  tables: [
    {
      table_id: 'table_1',
      caption: 'DSC Onset Temperatures for Material X Under Various Shear Conditions',
      headers: ['Condition', 'Onset (C)', 'Peak (C)', 'DH (J/g)'],
      row_count: 5,
    },
    {
      table_id: 'table_2',
      caption: 'Recommended Operating Limits for Material X',
      headers: ['RPM Range', 'Max Safe Temp', 'Safety Margin'],
      row_count: 3,
    },
  ],
  figures: [
    {
      figure_id: 'fig_1',
      type: 'line_chart',
      semantic_summary:
        'The decomposition rate of Material X increases sharply above 180C, with thermal runaway occurring beyond 200C.',
    },
    {
      figure_id: 'fig_1',
      type: 'line_chart',
      semantic_summary:
        'Temperature vs Decomposition Rate showing inflection point at ~180C and thermal runaway zone >200C.',
    },
  ],
};

export const mockKnowledgeResults: Record<string, IngestResponse> = {
  'paper-a': mockIngestResponse,
  'report-a': {
    doc_id: 'report-a-material-x-kneading',
    doc_title: 'Experimental Report: Material X Kneading Trials',
    pages_processed: 3,
    chunks_created: 16,
    chunk_distribution: { text: 6, table_row: 10, figure: 0 },
    tables: [
      {
        table_id: 'table_1',
        caption: 'Material X Kneading Results: 8 trial conditions',
        headers: ['#', 'Material', 'RPM', 'Jacket(C)', 'Discharge(C)', 'Quality'],
        row_count: 8,
      },
      {
        table_id: 'table_2',
        caption: 'Quality Assessment Summary',
        headers: ['Trial', 'Visual', 'Temp Check', 'Overall'],
        row_count: 8,
      },
    ],
    figures: [],
  },
  'paper-b': {
    doc_id: 'paper-b-equipment-a-mixing',
    doc_title: 'Continuous Mixer Design: Blade Configuration Effects on Discharge Temperature',
    pages_processed: 5,
    chunks_created: 19,
    chunk_distribution: { text: 12, table_row: 6, figure: 1 },
    tables: [
      {
        table_id: 'table_1',
        caption: 'Blade Type vs Energy Input (7 configurations)',
        headers: ['Blade Type', 'Energy (kW/kg)', 'Mixing Index', 'Recommendation'],
        row_count: 7,
      },
      {
        table_id: 'table_2',
        caption: 'Optimal Zone Length for Material Classes',
        headers: ['Material Class', 'Viscosity Range', 'Zone Length', 'Notes'],
        row_count: 6,
      },
    ],
    figures: [
      {
        figure_id: 'fig_1',
        type: 'bar_chart',
        semantic_summary:
          'Discharge temperature profile across 7 blade types at fixed RPM and inlet rate.',
      },
    ],
  },
};

// ===== Search — 3 query-specific responses =====

export const mockSearchResults: Record<string, SearchResponse> = {
  'Material X safe temperature': {
    query: 'Material X safe temperature',
    results: [
      {
        chunk_id: 'report-a_p2_c10',
        chunk_type: 'text',
        chunk_text:
          'Tests #5, #7, #8 exceeded thermal stability limit. Recommend max 180C for Material X processing. Test #7 (120 RPM, jacket 100C) reached 205C with visible brown discoloration.',
        doc_id: 'report-a-material-x-kneading',
        doc_title: 'Experimental Report: Material X Kneading Trials',
        page_number: 2,
        similarity: 0.873,
        search_method: 'hybrid',
      },
      {
        chunk_id: 'paper-a_p3_c12',
        chunk_type: 'figure',
        chunk_text:
          'The decomposition rate of Material X increases sharply above 180C, with thermal runaway occurring beyond 200C. Key data points: Inflection point ~180C; Thermal runaway zone >200C',
        doc_id: 'paper-a-material-x-thermal-stability',
        doc_title: 'Thermal Stability Analysis of Material X in High-Shear Mixing Processes',
        page_number: 3,
        similarity: 0.874,
        search_method: 'hybrid',
      },
      {
        chunk_id: 'paper-a_p2_t1r3',
        chunk_type: 'table_row',
        chunk_text:
          'Table table_1 | Condition: After 60rpm | Onset (C): 188 | Peak (C): 215 | DH (J/g): 285',
        doc_id: 'paper-a-material-x-thermal-stability',
        doc_title: 'Thermal Stability Analysis of Material X in High-Shear Mixing Processes',
        page_number: 2,
        similarity: 0.855,
        search_method: 'hybrid',
      },
    ],
    answer:
      'The safe temperature limit for Material X is 180C regardless of RPM setting. DSC analysis shows onset of exothermic decomposition at 188C (60 RPM). Processing above 200C risks thermal runaway. (Source: Experimental Report: Material X Kneading Trials, p.2)',
    sources: ['Experimental Report: Material X Kneading Trials, p.2', 'Thermal Stability Analysis, p.3'],
    total_results: 3,
    search_meta: { vector_hits: 10, bm25_hits: 9, search_time_ms: 1949 },
  },

  'Material X 60rpm onset temperature': {
    query: 'Material X 60rpm onset temperature',
    results: [
      {
        chunk_id: 'paper-a_p2_t1r2',
        chunk_type: 'table_row',
        chunk_text:
          'Table table_1 | Condition: After 60rpm | Onset (C): 188 | Peak (C): 215 | DH (J/g): 285',
        doc_id: 'paper-a-material-x-thermal-stability',
        doc_title: 'Thermal Stability Analysis of Material X in High-Shear Mixing Processes',
        page_number: 2,
        similarity: 0.891,
        search_method: 'hybrid',
      },
      {
        chunk_id: 'paper-a_p3_c13',
        chunk_type: 'text',
        chunk_text:
          'Based on the DSC onset temperatures, recommended operating limits were established with a 20C safety margin below the measured onset values.',
        doc_id: 'paper-a-material-x-thermal-stability',
        doc_title: 'Thermal Stability Analysis of Material X in High-Shear Mixing Processes',
        page_number: 3,
        similarity: 0.867,
        search_method: 'hybrid',
      },
    ],
    answer:
      'At 60rpm, DSC onset temperature for Material X is 188C with peak at 215C. The 20C safety margin yields a recommended maximum of 168C for 60rpm operation. As-received onset is 198C, dropping to 188C after 60rpm processing. (Source: Paper-A, Table 1)',
    sources: ['Thermal Stability Analysis, p.2, Table 1', 'Thermal Stability Analysis, p.3'],
    total_results: 2,
    search_meta: { vector_hits: 10, bm25_hits: 8, search_time_ms: 1623 },
  },

  'blade type recommendation for high viscosity': {
    query: 'blade type recommendation for high viscosity',
    results: [
      {
        chunk_id: 'paper-b_p2_c5',
        chunk_type: 'text',
        chunk_text:
          'For high-viscosity materials (>10,000 cP), Type A blades provide optimal shear distribution. Type C and D blades showed 15-20% higher energy consumption without significant improvement in mixing uniformity.',
        doc_id: 'paper-b-equipment-a-mixing',
        doc_title: 'Continuous Mixer Design: Blade Configuration Effects on Discharge Temperature',
        page_number: 2,
        similarity: 0.882,
        search_method: 'hybrid',
      },
      {
        chunk_id: 'paper-b_p3_t2r1',
        chunk_type: 'table_row',
        chunk_text:
          'Table table_2 | Blade Type: A | Viscosity Range: 5000-50000 cP | Energy (kW/kg): 0.42 | Mixing Index: 0.94 | Recommendation: Preferred',
        doc_id: 'paper-b-equipment-a-mixing',
        doc_title: 'Continuous Mixer Design: Blade Configuration Effects on Discharge Temperature',
        page_number: 3,
        similarity: 0.851,
        search_method: 'hybrid',
      },
    ],
    answer:
      'For high-viscosity materials, Type A blades are recommended. They provide optimal shear distribution with lowest energy consumption (0.42 kW/kg) and highest mixing index (0.94). Type C and D blades consume 15-20% more energy without improving uniformity. (Source: Paper-B, Table 2)',
    sources: ['Continuous Mixer Design, p.2', 'Continuous Mixer Design, p.3, Table 2'],
    total_results: 2,
    search_meta: { vector_hits: 10, bm25_hits: 7, search_time_ms: 1387 },
  },
};

// Legacy single-response export (kept for backward compat)
export const mockSearchResponse: SearchResponse = mockSearchResults['Material X safe temperature'];

export const mockFusionMLOnly: FusionResponse = {
  mode: 'ml_only',
  prediction: {
    discharge_temp_celsius: 234.2,
    d50_micron: null,
    confidence: 0.954,
    model: 'RandomForest-EquipmentA-v1',
  },
  shap: {
    top_factors: [
      { feature: 'jacket_temp', value: 210, shap_value: 69.59, direction: 'increases' },
      { feature: 'rpm', value: 100, shap_value: 10.88, direction: 'increases' },
      { feature: 'input_rate', value: 25, shap_value: -0.41, direction: 'decreases' },
      { feature: 'machine_prop_a', value: 50, shap_value: 0.35, direction: 'increases' },
      { feature: 'blade_type', value: 0, shap_value: -0.22, direction: 'decreases' },
    ],
    base_value: 153.8,
    explanation: 'jacket_temp contributes most (+69.59) to the prediction.',
  },
  domain_knowledge: null,
  fusion: null,
  safety_overrides: [],
  requires_human_review: true,
  meta: { total_time_ms: 4 },
};

export const mockFusionFusion: FusionResponse = {
  mode: 'fusion',
  prediction: {
    discharge_temp_celsius: 234.2,
    d50_micron: null,
    confidence: 0.954,
    model: 'RandomForest-EquipmentA-v1',
  },
  shap: {
    top_factors: [
      { feature: 'jacket_temp', value: 210, shap_value: 69.59, direction: 'increases' },
      { feature: 'rpm', value: 100, shap_value: 10.88, direction: 'increases' },
      { feature: 'input_rate', value: 25, shap_value: -0.41, direction: 'decreases' },
      { feature: 'machine_prop_a', value: 50, shap_value: 0.35, direction: 'increases' },
      { feature: 'blade_type', value: 0, shap_value: -0.22, direction: 'decreases' },
    ],
    base_value: 153.8,
    explanation: 'jacket_temp contributes most (+69.59) to the prediction.',
  },
  domain_knowledge: {
    rag_hits: 5,
    top_results: [
      {
        source: 'Experimental Report: Material X Kneading Trials',
        page: 2,
        similarity: 0.8782,
        text: 'Maximum processing temperature for Material X: 180C regardless of RPM setting. For RPM > 90, jacket temperature should not exceed 25C.',
      },
      {
        source: 'Thermal Stability Analysis of Material X in High-Shear Mixing Processes',
        page: 3,
        similarity: 0.868,
        text: 'The decomposition rate of Material X increases sharply above 180C, with thermal runaway occurring beyond 200C.',
      },
      {
        source: 'Experimental Report: Material X Kneading Trials',
        page: 1,
        similarity: 0.859,
        text: 'Table table_1 | #: 7 | Material: X | RPM: 120 | Jacket(C): 100 | Discharge(C): 205 | Quality: FAIL',
      },
    ],
  },
  fusion: {
    fused_prediction: 180,
    correction_applied: true,
    correction_delta: -54.2,
    correction_reason:
      'ML prediction (234.2C) exceeds thermal runaway threshold (200C) documented in Paper-A. Corrected to maximum safe temperature (180C) per domain literature.',
    domain_evidence: [
      'Experimental Report p.2: max 180C recommended',
      'Paper-A p.3: thermal runaway onset > 200C',
    ],
    risk_level: 'CRITICAL',
    recommendation:
      'Do NOT process at 210C with 100rpm. Reduce to 180C or lower. Consult safety team before proceeding.',
    confidence_score: 0.95,
    fusion_method: 'llm_fusion',
  },
  safety_overrides: [],
  requires_human_review: true,
  meta: { total_time_ms: 3740 },
};
