import { useEffect, useState } from 'react';
import { Zap } from 'lucide-react';
import InputForm from '../components/fusion/InputForm';
import ModeToggle from '../components/fusion/ModeToggle';
import MLPanel from '../components/fusion/MLPanel';
import DomainPanel from '../components/fusion/DomainPanel';
import FusionPanel from '../components/fusion/FusionPanel';
import useFusion from '../hooks/useFusion';
import { useApp } from '../contexts/AppContext';

export default function FusionPage() {
  const { t } = useApp();
  const { mode, setMode, predict, loading, result, error, lastRequest } =
    useFusion();

  // Track last submitted material + classifierRpm for MLPanel physics accuracy
  const [lastMaterial, setLastMaterial] = useState('Material A');
  const [lastClassifierRpm, setLastClassifierRpm] = useState(8000);

  // WHY: Re-fetch when mode toggles (only if previous request exists)
  useEffect(() => {
    if (lastRequest) {
      predict({ ...lastRequest, mode });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode]);

  const handlePredict = (
    material: string,
    conditions: Record<string, number | string>
  ) => {
    setLastMaterial(material);
    if (conditions.classifier_rpm != null) {
      setLastClassifierRpm(Number(conditions.classifier_rpm));
    }
    predict({ material, conditions, mode });
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t.fusion.title}
      </h1>
      <p className="text-gray-500 text-sm mt-1">
        {t.fusion.subtitle}
      </p>

      <InputForm onPredict={handlePredict} loading={loading} />

      {/* Mode toggle */}
      <div className="flex items-center justify-center gap-4 my-6">
        <span
          className={`text-sm font-medium ${
            mode === 'ml_only'
              ? 'text-gray-900 dark:text-white'
              : 'text-gray-400'
          }`}
        >
          {t.fusion.mlOnly}
        </span>
        <ModeToggle mode={mode} onToggle={setMode} />
        <span
          className={`text-sm font-medium ${
            mode === 'fusion'
              ? 'text-orange-600 dark:text-orange-400'
              : 'text-gray-400'
          }`}
        >
          {t.fusion.fusionMode}
        </span>
      </div>

      {error && (
        <div className="mb-4 rounded-xl bg-red-500/5 border border-red-500/20 p-3 text-sm text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      {!result && !loading && (
        <div className="flex flex-col items-center gap-3 py-16 text-gray-400">
          <Zap size={48} strokeWidth={1} />
          <p className="text-sm font-medium">{t.fusion.enterConditions}</p>
          <p className="text-xs">{t.fusion.tryQuickScenario}</p>
        </div>
      )}

      {result && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <MLPanel
              prediction={result.prediction}
              shap={result.shap}
              material={lastMaterial}
              classifierRpm={lastClassifierRpm}
            />
            <DomainPanel
              mode={result.mode}
              domainKnowledge={result.domain_knowledge}
              fusion={result.fusion}
            />
            <FusionPanel
              mode={result.mode}
              fusion={result.fusion}
              safetyOverrides={result.safety_overrides}
              totalTimeMs={result.meta.total_time_ms}
            />
          </div>

          <div
            className={`mt-4 p-3 rounded-xl text-center text-sm font-medium ${
              result.mode === 'ml_only'
                ? 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/20'
                : 'bg-orange-500/10 text-orange-700 dark:text-orange-300 border border-orange-500/20'
            }`}
          >
            {result.mode === 'ml_only'
              ? t.fusion.mlPredictionOnly
              : `${t.fusion.humanReview} \u2014 ${Math.round(result.meta.total_time_ms)}ms`}
          </div>
        </>
      )}
    </div>
  );
}
