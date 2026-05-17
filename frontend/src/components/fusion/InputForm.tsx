import { useState } from 'react';
import { Loader2, Zap, CheckCircle, AlertTriangle } from 'lucide-react';
import { useApp } from '../../contexts/AppContext';

// WHY: Slider range matches training data min/max to prevent extrapolation.
//      ML model reliability degrades sharply outside training range.
// INTERVIEW: "Slider bounds = training data bounds. Structural extrapolation prevention."

interface Props {
  onPredict: (material: string, conditions: Record<string, number | string>) => void;
  loading: boolean;
}

interface SliderConfig {
  min: number;
  max: number;
  step: number;
  default: number;
  unit: string;
  labelKey: string;
}

type EquipmentType = 'Equipment A' | 'Equipment B';

const EQUIPMENT_MATERIALS: Record<EquipmentType, string[]> = {
  'Equipment A': ['Material A', 'Material B', 'Material C', 'Material D', 'Material E', 'Material F'],
  'Equipment B': ['Material G', 'Material H', 'Material I', 'Material J', 'Material K', 'Material L', 'Material M', 'Material N'],
};

const SLIDER_RANGES: Record<EquipmentType, Record<string, SliderConfig>> = {
  'Equipment A': {
    temperature_celsius: { min: 25, max: 200, step: 1, default: 150, unit: '°C', labelKey: 'temperature' },
    rpm:                 { min: 30, max: 120, step: 1, default: 60, unit: '', labelKey: 'rpm' },
    input_rate_kg_h:     { min: 5, max: 50, step: 1, default: 25, unit: 'kg/h', labelKey: 'inputRate' },
    machine_prop_a:      { min: 1, max: 100, step: 1, default: 50, unit: '', labelKey: 'machinePropA' },
    machine_prop_b:      { min: 1, max: 100, step: 1, default: 50, unit: '', labelKey: 'machinePropB' },
    machine_prop_c:      { min: 1, max: 100, step: 1, default: 50, unit: '', labelKey: 'machinePropC' },
  },
  'Equipment B': {
    feed_rate_kg_h:        { min: 5, max: 49, step: 1, default: 10, unit: 'kg/h', labelKey: 'feedRate' },
    grinding_pressure_mpa: { min: 0.3, max: 1.2, step: 0.1, default: 0.6, unit: 'MPa', labelKey: 'pressure' },
    classifier_rpm:        { min: 2000, max: 10000, step: 100, default: 8000, unit: '', labelKey: 'classifierRpm' },
    air_flow:              { min: 5, max: 49, step: 1, default: 30, unit: 'm³/min', labelKey: 'airFlow' },
    bulk_density:          { min: 0.2, max: 2.0, step: 0.1, default: 0.8, unit: 'g/cm³', labelKey: 'bulkDensity' },
  },
};

const BLADE_TYPES = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];

interface PresetConfig {
  labelKey: string;
  labelFallback: string;
  icon: typeof CheckCircle;
  color: string;
  material: string;
  values: Record<string, number | string>;
}

const PRESETS: Record<EquipmentType, PresetConfig[]> = {
  'Equipment A': [
    {
      labelKey: 'safe',
      labelFallback: '150°C, 60rpm',
      icon: CheckCircle,
      color: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
      material: 'Material A',
      values: {
        temperature_celsius: 150, rpm: 60, input_rate_kg_h: 25,
        blade_type: 'A', machine_prop_a: 50, machine_prop_b: 50, machine_prop_c: 50,
      },
    },
    {
      labelKey: 'overload',
      labelFallback: '210°C, 100rpm',
      icon: AlertTriangle,
      color: 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20',
      material: 'Material A',
      values: {
        temperature_celsius: 210, rpm: 100, input_rate_kg_h: 40,
        blade_type: 'A', machine_prop_a: 80, machine_prop_b: 80, machine_prop_c: 80,
      },
    },
  ],
  'Equipment B': [
    {
      labelKey: 'safe',
      labelFallback: '0.6MPa, 8000rpm',
      icon: CheckCircle,
      color: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
      material: 'Material G',
      values: {
        feed_rate_kg_h: 10, grinding_pressure_mpa: 0.6, classifier_rpm: 8000, air_flow: 30, bulk_density: 0.8,
      },
    },
    {
      labelKey: 'overload',
      labelFallback: '1.1MPa, 3000rpm',
      icon: AlertTriangle,
      color: 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20',
      material: 'Material G',
      values: {
        feed_rate_kg_h: 45, grinding_pressure_mpa: 1.1, classifier_rpm: 3000, air_flow: 45, bulk_density: 1.5,
      },
    },
  ],
};

function buildDefaults(equipment: EquipmentType): Record<string, number | string> {
  const ranges = SLIDER_RANGES[equipment];
  const defaults: Record<string, number | string> = {};
  for (const [key, cfg] of Object.entries(ranges)) {
    defaults[key] = cfg.default;
  }
  if (equipment === 'Equipment A') {
    defaults.blade_type = 'A';
  }
  return defaults;
}

function SliderField({
  label,
  config,
  value,
  onChange,
}: {
  label: string;
  config: SliderConfig;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="text-xs font-medium text-gray-500 dark:text-gray-400">
          {label}
        </label>
        <span className="text-xs font-semibold text-gray-900 dark:text-white">
          {value}{config.unit && ` ${config.unit}`}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-[10px] text-gray-400 w-10 text-right shrink-0">
          {config.min}
        </span>
        <input
          type="range"
          min={config.min}
          max={config.max}
          step={config.step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full h-1.5 rounded-full appearance-none cursor-pointer
                     bg-gray-200 dark:bg-gray-600
                     accent-blue-600 dark:accent-blue-400"
        />
        <span className="text-[10px] text-gray-400 w-10 shrink-0">
          {config.max}
        </span>
      </div>
    </div>
  );
}

const selectClass =
  'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-xl ' +
  'bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm ' +
  'focus:ring-2 focus:ring-blue-500 focus:border-transparent';

export default function InputForm({ onPredict, loading }: Props) {
  const { t } = useApp();
  const [equipment, setEquipment] = useState<EquipmentType>('Equipment A');
  const [material, setMaterial] = useState('Material A');
  const [conditions, setConditions] = useState<Record<string, number | string>>(
    buildDefaults('Equipment A')
  );

  const handleEquipmentChange = (eq: EquipmentType) => {
    setEquipment(eq);
    setMaterial(EQUIPMENT_MATERIALS[eq][0]);
    setConditions(buildDefaults(eq));
  };

  const updateCondition = (key: string, value: number | string) => {
    setConditions((prev) => ({ ...prev, [key]: value }));
  };

  const applyPreset = (preset: PresetConfig) => {
    setMaterial(preset.material);
    setConditions((prev) => ({ ...prev, ...preset.values }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onPredict(material, conditions);
  };

  const sliderRanges = SLIDER_RANGES[equipment];
  const fusionT = t.fusion;

  const getLabel = (key: string): string => {
    return (fusionT as Record<string, string>)[key] || key;
  };

  return (
    <div className="mt-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs text-gray-500 dark:text-gray-400">{fusionT.quickScenario}:</span>
        {PRESETS[equipment].map((p) => {
          const label = `${getLabel(p.labelKey)} (${p.labelFallback})`;
          return (
            <button
              key={p.labelFallback}
              onClick={() => applyPreset(p)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all hover:opacity-80 ${p.color}`}
            >
              <p.icon size={13} />
              {label}
            </button>
          );
        })}
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5"
      >
        <div className="grid grid-cols-2 gap-4 mb-5">
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              {fusionT.equipmentType}
            </label>
            <select
              value={equipment}
              onChange={(e) => handleEquipmentChange(e.target.value as EquipmentType)}
              className={selectClass}
            >
              <option value="Equipment A">Equipment A</option>
              <option value="Equipment B">Equipment B</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              {fusionT.material}
            </label>
            <select
              value={material}
              onChange={(e) => setMaterial(e.target.value)}
              className={selectClass}
            >
              {EQUIPMENT_MATERIALS[equipment].map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
          {Object.entries(sliderRanges).map(([key, config]) => (
            <SliderField
              key={key}
              label={getLabel(config.labelKey)}
              config={config}
              value={conditions[key] as number}
              onChange={(v) => updateCondition(key, v)}
            />
          ))}

          {equipment === 'Equipment A' && (
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                {fusionT.bladeType}
              </label>
              <select
                value={conditions.blade_type as string}
                onChange={(e) => updateCondition('blade_type', e.target.value)}
                className={selectClass}
              >
                {BLADE_TYPES.map((b) => (
                  <option key={b} value={b}>Type {b}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="mt-5 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm
                       hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
                       flex items-center gap-2 transition-colors"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
            {fusionT.predict}
          </button>
        </div>
      </form>
    </div>
  );
}
