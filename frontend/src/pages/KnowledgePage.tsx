import { useState } from 'react';
import { FileText } from 'lucide-react';
import DropZone from '../components/knowledge/DropZone';
import ExtractionCard from '../components/knowledge/ExtractionCard';
import useKnowledgeIngest from '../hooks/useKnowledgeIngest';
import { useApp } from '../contexts/AppContext';
import type { IngestResponse } from '../types/api';
import { mockKnowledgeResults } from '../mocks/mockData';

const SAMPLE_KEYS = ['paper-a', 'report-a', 'paper-b'] as const;

export default function KnowledgePage() {
  const { t, isDemo } = useApp();
  const { ingest, loading, result: hookResult, error } = useKnowledgeIngest();
  const [sampleResult, setSampleResult] = useState<IngestResponse | null>(null);

  const result = sampleResult ?? hookResult;

  const handleSample = (key: string) => {
    setSampleResult(mockKnowledgeResults[key]);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t.knowledge.title}
      </h1>
      <p className="text-gray-500 text-sm mt-1">
        {t.knowledge.subtitle}
      </p>

      <DropZone onUpload={ingest} loading={loading} />

      {isDemo && !loading && (
        <div className="flex items-center gap-2 mt-4 flex-wrap">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {t.knowledge.trySample}
          </span>
          {SAMPLE_KEYS.map((key) => (
            <button
              key={key}
              onClick={() => handleSample(key)}
              className="px-3 py-1.5 rounded-full text-xs font-medium border transition-all
                         bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20
                         hover:bg-purple-500/20 cursor-pointer"
            >
              {t.knowledge[`sample_${key.replace('-', '_')}` as keyof typeof t.knowledge]}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-xl bg-red-500/5 border border-red-500/20 p-3 text-sm text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      {!result && !loading && !isDemo && (
        <div className="flex flex-col items-center gap-3 py-16 text-gray-400">
          <FileText size={48} strokeWidth={1} />
          <p className="text-sm font-medium">{t.knowledge.uploadPrompt}</p>
          <p className="text-xs">{t.knowledge.vlmExtract}</p>
        </div>
      )}

      {!result && !loading && isDemo && (
        <div className="flex flex-col items-center gap-3 py-12 text-gray-400">
          <FileText size={48} strokeWidth={1} />
          <p className="text-sm font-medium">{t.knowledge.uploadPrompt}</p>
          <p className="text-xs">{t.knowledge.vlmExtract}</p>
        </div>
      )}

      {result && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <ExtractionCard type="text" data={result} />
          <ExtractionCard type="table" data={result} />
          <ExtractionCard type="figure" data={result} />
          <ExtractionCard type="status" data={result} />
        </div>
      )}
    </div>
  );
}
