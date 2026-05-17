import { useState } from 'react';
import { Search } from 'lucide-react';
import SearchBar from '../components/search/SearchBar';
import AnswerBox from '../components/search/AnswerBox';
import ResultCard from '../components/search/ResultCard';
import useSearch from '../hooks/useSearch';
import { useApp } from '../contexts/AppContext';

const SEARCH_EXAMPLES = [
  'Material X safe temperature',
  'Material X 60rpm onset temperature',
  'blade type recommendation for high viscosity',
];

export default function SearchPage() {
  const { t } = useApp();
  const { search, loading, result, error } = useSearch();
  const [, setQuery] = useState('');

  const handleExampleClick = (example: string) => {
    setQuery(example);
    search(example);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t.search.title}
      </h1>
      <p className="text-gray-500 text-sm mt-1">
        {t.search.subtitle}
      </p>

      <SearchBar onSearch={search} loading={loading} />

      <div className="mt-3 flex items-center gap-2 flex-wrap">
        <span className="text-xs text-gray-500 dark:text-gray-400">{t.search.examples}</span>
        {SEARCH_EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => handleExampleClick(ex)}
            className="px-3 py-1.5 rounded-full text-xs font-medium border transition-all
                       bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20
                       hover:bg-blue-500/20 cursor-pointer"
          >
            {ex.length > 40 ? ex.slice(0, 40) + '...' : ex}
          </button>
        ))}
      </div>

      {error && (
        <div className="mt-4 rounded-xl bg-red-500/5 border border-red-500/20 p-3 text-sm text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      {!result && !loading && (
        <div className="flex flex-col items-center gap-3 py-16 text-gray-400">
          <Search size={48} strokeWidth={1} />
          <p className="text-sm font-medium">{t.search.searchPrompt}</p>
          <p className="text-xs">{t.search.tryExamples}</p>
        </div>
      )}

      {result && (
        <>
          {result.answer && (
            <AnswerBox
              answer={result.answer}
              sources={result.sources}
              meta={result.search_meta}
            />
          )}

          <div className="space-y-4 mt-6">
            {result.results.map((r) => (
              <ResultCard key={r.chunk_id} result={r} />
            ))}
          </div>

          <p className="text-sm text-gray-400 mt-4 font-mono">
            {result.total_results} results
          </p>
        </>
      )}
    </div>
  );
}
