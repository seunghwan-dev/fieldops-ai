import type { FusionResponse } from '../../types/api';
import { useApp } from '../../contexts/AppContext';
import ShapChart from './ShapChart';

// WHY: Material-specific RPM thresholds for physics formula reliability.
// INTERVIEW: "Material G is accurate above 6000rpm, Material I needs 5000+.
//             Traffic light makes it instantly visible."
const PHYSICS_ACCURACY_THRESHOLDS: Record<string, { reliable: number; moderate: number }> = {
  'Material G': { reliable: 6000, moderate: 4000 },
  'Material H': { reliable: 7000, moderate: 5000 },
  'Material I': { reliable: 5000, moderate: 3000 },
  'Material J': { reliable: 6000, moderate: 4000 },
  'Material K': { reliable: 6500, moderate: 4500 },
  'Material L': { reliable: 5500, moderate: 3500 },
  'Material M': { reliable: 6000, moderate: 4000 },
  'Material N': { reliable: 7000, moderate: 5000 },
};

const DEFAULT_THRESHOLD = { reliable: 6000, moderate: 4000 };

interface PhysicsAccuracy {
  level: 'HIGH' | 'MODERATE' | 'LOW';
  ratio: number;
  barColor: string;
  bgColor: string;
  borderColor: string;
}

function getPhysicsAccuracy(
  material: string,
  classifierRpm: number,
  correctionRatio: number
): PhysicsAccuracy {
  const thresholds = PHYSICS_ACCURACY_THRESHOLDS[material] ?? DEFAULT_THRESHOLD;

  if (classifierRpm >= thresholds.reliable && correctionRatio < 15) {
    return { level: 'HIGH', ratio: correctionRatio,
      barColor: 'bg-emerald-500', bgColor: 'bg-emerald-500/10', borderColor: 'border-emerald-500/20' };
  } else if (classifierRpm >= thresholds.moderate && correctionRatio < 30) {
    return { level: 'MODERATE', ratio: correctionRatio,
      barColor: 'bg-yellow-500', bgColor: 'bg-yellow-500/10', borderColor: 'border-yellow-500/20' };
  }
  return { level: 'LOW', ratio: correctionRatio,
    barColor: 'bg-red-500', bgColor: 'bg-red-500/10', borderColor: 'border-red-500/20' };
}

const LEVEL_EMOJI: Record<string, string> = { HIGH: '🟢', MODERATE: '🟡', LOW: '🔴' };
const LEVEL_TEXT_COLOR: Record<string, string> = {
  HIGH: 'text-emerald-600 dark:text-emerald-400',
  MODERATE: 'text-yellow-600 dark:text-yellow-400',
  LOW: 'text-red-600 dark:text-red-400',
};

interface Props {
  prediction: FusionResponse['prediction'];
  shap: FusionResponse['shap'];
  material?: string;
  classifierRpm?: number;
}

export default function MLPanel({ prediction, shap, material, classifierRpm }: Props) {
  const { t } = useApp();
  const isMixer = prediction.discharge_temp_celsius != null;
  const mainValue = isMixer
    ? prediction.discharge_temp_celsius
    : prediction.d50_micron;
  const unit = isMixer ? '°C' : 'μm';

  const showPhysics = !isMixer && prediction.physics_only_d50 != null && prediction.ml_correction != null;
  let accuracy: PhysicsAccuracy | null = null;

  if (showPhysics) {
    const physicsVal = Math.abs(prediction.physics_only_d50!);
    const correctionVal = Math.abs(prediction.ml_correction!);
    const correctionRatio = physicsVal > 0 ? (correctionVal / physicsVal) * 100 : 0;
    accuracy = getPhysicsAccuracy(
      material || 'Material G',
      classifierRpm || 8000,
      correctionRatio
    );
  }

  const getPhysicsMessage = (acc: PhysicsAccuracy, rpm: number): string => {
    const templateKey = acc.level === 'HIGH' ? 'physicsHigh'
      : acc.level === 'MODERATE' ? 'physicsModerate' : 'physicsLow';
    const template = t.fusion[templateKey];
    return template
      .replace('{rpm}', String(rpm))
      .replace('{ratio}', acc.ratio.toFixed(0));
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 animate-fade-in">
      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
        {t.fusion.mlPrediction}
      </h3>

      <p className="text-4xl font-bold text-gray-900 dark:text-white">
        {mainValue != null ? mainValue : '—'}
        <span className="text-lg font-normal text-gray-500 ml-1">{unit}</span>
      </p>

      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
        {t.fusion.confidence}:{' '}
        <span className="font-medium text-gray-700 dark:text-gray-300">
          {(prediction.confidence * 100).toFixed(1)}%
        </span>
      </p>

      {showPhysics && (
        <div className="mt-3 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-xs space-y-1">
          <p>
            Physics:{' '}
            <span className="font-medium">{prediction.physics_only_d50} μm</span>
          </p>
          <p>
            ML {t.fusion.correction}:{' '}
            <span className="font-medium">{prediction.ml_correction} μm</span>
          </p>
          {prediction.physics_formula && (
            <p className="text-gray-400">{prediction.physics_formula}</p>
          )}
        </div>
      )}

      {accuracy && (
        <div className={`mt-3 p-3 rounded-lg border ${accuracy.bgColor} ${accuracy.borderColor}`}>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm">{LEVEL_EMOJI[accuracy.level]}</span>
            <span className={`text-xs font-bold uppercase ${LEVEL_TEXT_COLOR[accuracy.level]}`}>
              {accuracy.level}
            </span>
            <span className="text-[10px] text-gray-500 dark:text-gray-400">
              — {t.fusion.physicsAccuracy}
            </span>
          </div>
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
            {getPhysicsMessage(accuracy, classifierRpm || 8000)}
          </p>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-blue-200 dark:bg-blue-900 rounded-full overflow-hidden">
              <div
                className={`h-full ${accuracy.barColor} rounded-full transition-all`}
                style={{ width: `${Math.min(accuracy.ratio, 100)}%`, float: 'right' }}
              />
            </div>
          </div>
          <div className="flex justify-between text-[10px] text-gray-400 mt-1">
            <span>Physics {(100 - accuracy.ratio).toFixed(0)}%</span>
            <span>ML {accuracy.ratio.toFixed(0)}%</span>
          </div>
        </div>
      )}

      <ShapChart factors={shap.top_factors} baseValue={shap.base_value} />

      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 italic">
        {shap.explanation}
      </p>

      <div className="mt-3 pt-2 border-t border-gray-100 dark:border-gray-700 font-mono text-xs text-gray-400">
        {prediction.model} · conf {(prediction.confidence * 100).toFixed(1)}%
      </div>
    </div>
  );
}
