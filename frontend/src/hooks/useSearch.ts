import { useState } from 'react';
import type { SearchResponse } from '../types/api';
import { useApp } from '../contexts/AppContext';
import { mockSearchResults, mockSearchResponse } from '../mocks/mockData';

export default function useSearch() {
  const { isDemo } = useApp();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const search = async (query: string) => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      if (isDemo) {
        await new Promise((r) => setTimeout(r, 1500));
        const matched = mockSearchResults[query];
        setResult(matched ?? { ...mockSearchResponse, query });
      } else {
        const res = await fetch(
          `/api/v1/knowledge/search?q=${encodeURIComponent(query)}`
        );
        if (!res.ok) throw new Error(`Search failed: ${res.status}`);
        const data = (await res.json()) as SearchResponse;
        setResult(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return { search, loading, result, error };
}
