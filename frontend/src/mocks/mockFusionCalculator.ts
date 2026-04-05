// Dynamic mock calculator for DEMO mode Fusion page.
// Produces slider-reactive predictions without a backend.

import type { FusionResponse } from '../types/api';

const EQUIP_B_MATERIALS = [
  'Material G', 'Material H', 'Material I', 'Material J',
  'Material K', 'Material L', 'Material M', 'Material N',
];

export function calculateMockFusion(
  material: string,
  conditions: Record<string, number | string>,
  mode: 'ml_only' | 'fusion',
): FusionResponse {
  if (EQUIP_B_MATERIALS.includes(material)) {
    return calculateGrinderMock(conditions, mode);
  }
  return calculateMixerMock(conditions, mode);
}

function calculateMixerMock(
  conditions: Record<string, number | string>,
  mode: 'ml_only' | 'fusion',
): FusionResponse {
  const temp = Number(conditions.temperature_celsius ?? 150);
  const rpm = Number(conditions.rpm ?? 60);
  const inputRate = Number(conditions.input_rate_kg_h ?? 25);
  const propA = Number(conditions.machine_prop_a ?? 50);

  const discharge =
    Math.round(
      (20 + 0.8 * temp + 0.5 * rpm + 0.1 * inputRate + 0.05 * propA +
        (Math.random() - 0.5) * 10) *
        10,
    ) / 10;
  const confidence = Math.round((0.90 + Math.random() * 0.08) * 1000) / 1000;

  const shapJacket = Math.round(0.8 * (temp - 100) * 100) / 100;
  const shapRpm = Math.round(0.5 * (rpm - 60) * 100) / 100;
  const shapInput = Math.round(0.1 * (inputRate - 25) * 100) / 100;

  const prediction = {
    discharge_temp_celsius: discharge,
    d50_micron: null,
    confidence,
    model: 'RandomForest-EquipmentA-v1',
  };

  const shap = {
    top_factors: [
      { feature: 'jacket_temp', value: temp, shap_value: shapJacket, direction: shapJacket >= 0 ? 'increases' : 'decreases' },
      { feature: 'rpm', value: rpm, shap_value: shapRpm, direction: shapRpm >= 0 ? 'increases' : 'decreases' },
      { feature: 'input_rate', value: inputRate, shap_value: shapInput, direction: shapInput >= 0 ? 'increases' : 'decreases' },
    ],
    base_value: 153.8,
    explanation: `jacket_temp contributes most (${shapJacket > 0 ? '+' : ''}${shapJacket}) to the prediction.`,
  };

  let fusion: FusionResponse['fusion'] = null;
  let domainKnowledge: FusionResponse['domain_knowledge'] = null;

  if (mode === 'fusion') {
    const riskLevel = discharge > 200 ? 'CRITICAL' : discharge > 180 ? 'MEDIUM' : 'LOW';
    const fused = discharge > 200 ? 180 : discharge > 180 ? discharge - 5 : discharge;
    const correctionDelta = Math.round((fused - discharge) * 10) / 10;

    domainKnowledge = {
      rag_hits: 5,
      top_results: [
        {
          source: 'Experimental Report: Material X Kneading Trials',
          page: 2,
          similarity: 0.88,
          text: 'Maximum processing temperature for Material X: 180C regardless of RPM setting.',
        },
        {
          source: 'Thermal Stability Analysis of Material X in High-Shear Mixing Processes',
          page: 3,
          similarity: 0.87,
          text: 'The decomposition rate increases sharply above 180C.',
        },
      ],
    };

    fusion = {
      fused_prediction: fused,
      correction_applied: correctionDelta !== 0,
      correction_delta: correctionDelta,
      correction_reason:
        discharge > 200
          ? `ML prediction (${discharge}C) exceeds thermal runaway threshold (200C). Corrected to 180C per domain literature.`
          : discharge > 180
            ? 'ML prediction slightly above recommended range. Minor correction applied.'
            : 'ML prediction within safe range. No correction needed.',
      domain_evidence:
        discharge > 180
          ? ['Experimental Report p.2: max 180C recommended', 'Paper-A p.3: thermal runaway onset > 200C']
          : [],
      risk_level: riskLevel,
      recommendation:
        discharge > 200
          ? `Do NOT process at ${Math.round(Number(conditions.temperature_celsius))}C with ${conditions.rpm}rpm. Reduce to 180C or lower.`
          : 'Operating conditions are within acceptable range.',
      confidence_score: 0.95,
      fusion_method: 'llm_fusion',
    };
  }

  return {
    mode,
    prediction,
    shap,
    domain_knowledge: domainKnowledge,
    fusion,
    safety_overrides: [],
    requires_human_review: true,
    meta: {
      total_time_ms: mode === 'fusion' ? 3500 + Math.random() * 500 : 4 + Math.random() * 5,
    },
  };
}

function calculateGrinderMock(
  conditions: Record<string, number | string>,
  mode: 'ml_only' | 'fusion',
): FusionResponse {
  const feedRate = Number(conditions.feed_rate_kg_h ?? 10);
  const pressure = Number(conditions.grinding_pressure_mpa ?? 0.6);
  const classifierRpm = Number(conditions.classifier_rpm ?? 8000);
  const airFlow = Number(conditions.air_flow ?? 30);
  const bulkDensity = Number(conditions.bulk_density ?? 0.8);

  // Bond's Law mock
  const K = 2.84;
  const dCut = K / (classifierRpm * Math.sqrt(pressure));
  const feedFactor = 1.0 + 0.02 * (feedRate - 10);
  const airFactor = 1.0 - 0.005 * (airFlow - 50);
  const densityFactor = 1.0 + 0.3 * (bulkDensity - 1.0);
  const physicsD50 = Math.round(dCut * feedFactor * airFactor * densityFactor * 1000 * 100) / 100;
  const mlCorrection = Math.round((Math.random() - 0.5) * 0.3 * 100) / 100;
  const d50 = Math.round(Math.max(physicsD50 + mlCorrection, 0.01) * 100) / 100;
  const confidence = Math.round((0.55 + Math.random() * 0.1) * 1000) / 1000;

  const prediction = {
    discharge_temp_celsius: null,
    d50_micron: d50,
    physics_only_d50: physicsD50,
    ml_correction: mlCorrection,
    physics_formula: "Bond's Law + classifier cut-point equation",
    confidence,
    model: 'BondsLaw+RandomForest-EquipmentB-v1',
  };

  const shap = {
    top_factors: [
      { feature: 'classifier_rpm', value: classifierRpm, shap_value: -0.09, direction: 'decreases' as const },
      { feature: 'feed_rate', value: feedRate, shap_value: 0.05, direction: 'increases' as const },
      { feature: 'air_flow', value: airFlow, shap_value: 0.03, direction: 'increases' as const },
      { feature: 'bulk_density', value: bulkDensity, shap_value: 0.02, direction: 'increases' as const },
    ],
    base_value: -0.1,
    explanation: 'ML error correction: classifier_rpm contributes most to the correction.',
  };

  return {
    mode,
    prediction,
    shap,
    domain_knowledge: mode === 'fusion' ? {
      rag_hits: 3,
      top_results: [
        {
          source: 'Experimental Report: Material Y Grinding',
          page: 1,
          similarity: 0.86,
          text: `Feed Rate: ${feedRate} kg/h, Pressure: ${pressure} MPa — conditions within acceptable range.`,
        },
      ],
    } : null,
    fusion: mode === 'fusion' ? {
      fused_prediction: d50,
      correction_applied: false,
      correction_delta: 0,
      correction_reason: 'No safety concern for particle size prediction.',
      domain_evidence: [],
      risk_level: 'LOW',
      recommendation: 'Operating conditions acceptable.',
      confidence_score: 0.80,
      fusion_method: 'llm_fusion',
    } : null,
    safety_overrides: [],
    requires_human_review: true,
    meta: {
      total_time_ms: mode === 'fusion' ? 3200 + Math.random() * 400 : 3 + Math.random() * 4,
    },
  };
}
