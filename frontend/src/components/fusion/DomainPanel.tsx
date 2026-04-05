import { Lock } from 'lucide-react';
import type { FusionResponse } from '../../types/api';
import { useApp } from '../../contexts/AppContext';

interface Props {
  mode: string;
  domainKnowledge: FusionResponse['domain_knowledge'];
  fusion: FusionResponse['fusion'];
}

const riskColors: Record<string, string> = {
  CRITICAL: 'bg-red-500 text-white',
  HIGH: 'bg-orange-500 text-white',
  MEDIUM: 'bg-yellow-400 text-yellow-900',
  LOW: 'bg-emerald-500/20 text-emerald-400',
};

function simBadge(sim: number) {
  if (sim >= 0.9) return 'text-emerald-500';
  if (sim >= 0.85) return 'text-yellow-500';
  return 'text-gray-400';
}

export default function DomainPanel({ mode, domainKnowledge, fusion }: Props) {
  const { t } = useApp();

  if (mode !== 'fusion' || !domainKnowledge) {
    return (
      <div className="bg-gray-50 dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 opacity-50 flex flex-col items-center justify-center min-h-[200px]">
        <Lock size={32} className="text-gray-400 mb-2" />
        <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">
          {t.fusion.enableFusion}
        </p>
        <p className="text-xs text-gray-400">{t.fusion.toSeeDomain}</p>
      </div>
    );
  }

  const riskLevel = fusion?.risk_level || 'MEDIUM';

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 animate-fade-in">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
          {t.fusion.domainKnowledge}
        </h3>
        <span
          className={`text-[10px] font-bold uppercase px-2.5 py-1 rounded ${riskColors[riskLevel] || riskColors.MEDIUM}`}
        >
          {riskLevel}
        </span>
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
        {domainKnowledge.rag_hits} RAG hits
      </p>

      <div className="space-y-2 max-h-60 overflow-y-auto">
        {domainKnowledge.top_results.slice(0, 3).map((r, i) => (
          <div
            key={i}
            className="p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-xs"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-medium text-gray-700 dark:text-gray-300 truncate max-w-[180px]">
                {r.source}
              </span>
              <div className="flex items-center gap-1.5 font-mono">
                <span className="text-gray-400">p.{r.page}</span>
                <span className={`font-semibold ${simBadge(r.similarity)}`}>
                  {(r.similarity * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <p className="text-gray-500 dark:text-gray-400 line-clamp-2">
              {r.text.slice(0, 150)}
            </p>
          </div>
        ))}
      </div>

      {fusion?.domain_evidence && fusion.domain_evidence.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
            {t.fusion.evidence}
          </p>
          <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
            {fusion.domain_evidence.map((e, i) => (
              <li key={i}>- {e}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
