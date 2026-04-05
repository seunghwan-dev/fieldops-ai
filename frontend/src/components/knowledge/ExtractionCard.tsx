import { FileText, Table, BarChart3, CheckCircle } from 'lucide-react';
import type { IngestResponse } from '../../types/api';

interface Props {
  type: 'text' | 'table' | 'figure' | 'status';
  data: IngestResponse | null;
}

const config = {
  text: { icon: FileText, title: 'Text Extracted', color: 'border-l-blue-500' },
  table: { icon: Table, title: 'Tables Detected', color: 'border-l-green-500' },
  figure: { icon: BarChart3, title: 'Figures Analyzed', color: 'border-l-purple-500' },
  status: { icon: CheckCircle, title: 'Processing Status', color: 'border-l-gray-500' },
};

export default function ExtractionCard({ type, data }: Props) {
  const { icon: Icon, title, color } = config[type];

  const renderContent = () => {
    if (!data) {
      return <p className="text-sm text-gray-400">Upload a PDF to see results</p>;
    }

    switch (type) {
      case 'text':
        return (
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {data.chunk_distribution.text}{' '}
            <span className="text-sm font-normal text-gray-500">chunks</span>
          </p>
        );
      case 'table':
        return (
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {data.tables.length}
            </p>
            {data.tables.map((t) => (
              <p key={t.table_id} className="text-xs text-gray-500 truncate mt-1">
                {t.caption || t.table_id} ({t.row_count} rows)
              </p>
            ))}
          </div>
        );
      case 'figure':
        return (
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {data.figures.length}
            </p>
            {data.figures.map((f) => (
              <p key={f.figure_id} className="text-xs text-gray-500 mt-1">
                {f.semantic_summary.slice(0, 120)}
              </p>
            ))}
          </div>
        );
      case 'status':
        return (
          <div className="space-y-1">
            <p className="text-sm">
              <span className="font-medium">{data.chunks_created}</span> chunks created
            </p>
            <p className="text-sm">
              <span className="font-medium">{data.pages_processed}</span> pages processed
            </p>
            <p className="text-sm text-green-600 font-medium">Oracle indexed</p>
          </div>
        );
    }
  };

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 border-l-4 ${color} p-4 ${
        data ? 'animate-fade-in' : 'opacity-50'
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        <Icon size={18} className="text-gray-500" />
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          {title}
        </h3>
      </div>
      {renderContent()}
    </div>
  );
}
