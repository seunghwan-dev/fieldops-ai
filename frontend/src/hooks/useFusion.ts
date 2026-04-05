import { useState } from 'react';
import type { FusionResponse } from '../types/api';
import { useApp } from '../contexts/AppContext';
import { calculateMockFusion } from '../mocks/mockFusionCalculator';

export default function useFusion() {
  const { isDemo } = useApp();
  const [mode, setModeState] = useState<'ml_only' | 'fusion'>('ml_only');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FusionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastRequest, setLastRequest] = useState<{
    material: string;
    conditions: Record<string, number | string>;
  } | null>(null);

  const predict = async (request: {
    material: string;
    conditions: Record<string, number | string>;
    mode: 'ml_only' | 'fusion';
  }) => {
    setLoading(true);
    setError(null);
    setLastRequest({ material: request.material, conditions: request.conditions });
    try {
      if (isDemo) {
        await new Promise((r) => setTimeout(r, request.mode === 'fusion' ? 2000 : 800));
        setResult(calculateMockFusion(request.material, request.conditions, request.mode));
      } else {
        const res = await fetch('/api/v1/fusion/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request),
        });
        if (!res.ok) throw new Error(`Prediction failed: ${res.status}`);
        const data = (await res.json()) as FusionResponse;
        setResult(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const setMode = (newMode: 'ml_only' | 'fusion') => {
    setModeState(newMode);
  };

  return { mode, setMode, predict, loading, result, error, lastRequest };
}
