import { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { useApp } from '../../contexts/AppContext';

interface Props {
  onSearch: (query: string) => void;
  loading: boolean;
}

export default function SearchBar({ onSearch, loading }: Props) {
  const { t } = useApp();
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={t.search.placeholder}
        disabled={loading}
        className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-xl
                   bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                   focus:ring-2 focus:ring-blue-500 focus:border-transparent
                   disabled:opacity-60 text-sm"
      />
      <button
        type="submit"
        disabled={loading || !query.trim()}
        className="px-5 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm
                   hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
                   flex items-center gap-2 transition-colors"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
        {t.search.searchButton}
      </button>
    </form>
  );
}
