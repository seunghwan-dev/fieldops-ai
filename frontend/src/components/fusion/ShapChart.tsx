import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { ShapFactor } from '../../types/api';

interface Props {
  factors: ShapFactor[];
  baseValue: number;
}

export default function ShapChart({ factors, baseValue }: Props) {
  if (!factors.length) return null;

  return (
    <div className="mt-4">
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
        SHAP Feature Importance (base: {baseValue.toFixed(1)})
      </p>
      <ResponsiveContainer width="100%" height={factors.length * 40 + 20}>
        <BarChart
          data={factors}
          layout="vertical"
          margin={{ left: 80, right: 20 }}
        >
          <XAxis type="number" tick={{ fontSize: 11 }} />
          <YAxis
            dataKey="feature"
            type="category"
            tick={{ fontSize: 11 }}
            width={75}
          />
          <Tooltip
            formatter={(value, _name, props) => {
              const v = Number(value);
              const p = props.payload as unknown as ShapFactor;
              return [
                `${v > 0 ? '+' : ''}${v.toFixed(2)}`,
                `${p.feature} = ${p.value}`,
              ];
            }}
          />
          <Bar dataKey="shap_value" radius={[0, 4, 4, 0]}>
            {factors.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.shap_value > 0 ? '#ef4444' : '#3b82f6'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="flex gap-4 text-xs text-gray-500 dark:text-gray-400 mt-1">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-red-500 rounded-sm inline-block" />{' '}
          Increases
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-blue-500 rounded-sm inline-block" />{' '}
          Decreases
        </span>
      </div>
    </div>
  );
}
