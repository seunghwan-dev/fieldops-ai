import type { SearchResult } from '../../types/api';

interface Props {
  result: SearchResult;
}

function similarityBadge(sim: number) {
  if (sim >= 0.9) return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
  if (sim >= 0.85) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300';
  return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
}

const typeColors: Record<string, string> = {
  text: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  table_row: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  figure: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
};

export default function ResultCard({ result }: Props) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow animate-fade-in">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate max-w-md">
            {result.doc_title}
          </h3>
          {result.page_number && (
            <span className="text-xs text-gray-500">p.{result.page_number}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${typeColors[result.chunk_type] || typeColors.text}`}>
            {result.chunk_type}
          </span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${similarityBadge(result.similarity)}`}>
            {(result.similarity * 100).toFixed(1)}%
          </span>
        </div>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
        {result.chunk_text.slice(0, 200)}
        {result.chunk_text.length > 200 && '...'}
      </p>
      <div className="mt-3 pt-2 border-t border-gray-100 dark:border-gray-700 font-mono text-xs text-gray-400">
        {result.search_method} · {result.doc_id} · p.{result.page_number} · {(result.similarity * 100).toFixed(1)}%
      </div>
    </div>
  );
}
