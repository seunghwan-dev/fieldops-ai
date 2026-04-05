import { Lock, AlertTriangle } from 'lucide-react';
import type { FusionResponse } from '../../types/api';
import { useApp } from '../../contexts/AppContext';

interface Props {
  mode: string;
  fusion: FusionResponse['fusion'];
  safetyOverrides: FusionResponse['safety_overrides'];
  totalTimeMs?: number;
}

export default function FusionPanel({ mode, fusion, safetyOverrides, totalTimeMs }: Props) {
  const { t } = useApp();

  if (mode !== 'fusion' || !fusion) {
    return (
      <div className="bg-gray-50 dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 opacity-50 flex flex-col items-center justify-center min-h-[200px]">
        <Lock size={32} className="text-gray-400 mb-2" />
        <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">
          {t.fusion.enableFusion}
        </p>
        <p className="text-xs text-gray-400">{t.fusion.toggleToSee}</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 animate-fade-in">
      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
        {t.fusion.fusionResult}
      </h3>

      <p className="text-4xl font-bold text-gray-900 dark:text-white">
        {fusion.fused_prediction}
        <span className="text-lg font-normal text-gray-500 ml-1">(fused)</span>
      </p>

      {fusion.correction_applied ? (
        <p className="text-sm mt-2">
          <span className="text-red-600 dark:text-red-400 font-medium">
            Correction: {fusion.correction_delta > 0 ? '+' : ''}
            {fusion.correction_delta.toFixed(1)}
          </span>
        </p>
      ) : (
        <p className="text-sm text-green-600 dark:text-green-400 font-medium mt-2">
          {t.fusion.noCorrection}
        </p>
      )}

      <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
        {fusion.correction_reason}
      </p>

      {fusion.recommendation && (
        <div className="mt-3 p-3 rounded-xl bg-red-500/5 border border-red-500/20 text-sm text-red-700 dark:text-red-300">
          {fusion.recommendation}
        </div>
      )}

      {safetyOverrides.length > 0 && (
        <div className="mt-3 space-y-2">
          {safetyOverrides.map((o, i) => (
            <div
              key={i}
              className="p-2 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-2"
            >
              <AlertTriangle size={16} className="text-red-500 mt-0.5 shrink-0" />
              <div className="text-xs">
                <span className="font-bold text-red-700 dark:text-red-300">
                  {o.rule_id} [{o.severity}]
                </span>
                <p className="text-red-600 dark:text-red-400">{o.message}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-3 pt-2 border-t border-gray-100 dark:border-gray-700 font-mono text-xs text-gray-400">
        {fusion.fusion_method} · {totalTimeMs ? `${Math.round(totalTimeMs)}ms` : ''} · conf {(fusion.confidence_score * 100).toFixed(0)}%
      </div>
    </div>
  );
}
