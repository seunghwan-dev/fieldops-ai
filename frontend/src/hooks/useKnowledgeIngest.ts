import { useState } from 'react';
import type { IngestResponse } from '../types/api';
import { useApp } from '../contexts/AppContext';
import { mockIngestResponse } from '../mocks/mockData';

export default function useKnowledgeIngest() {
  const { isDemo } = useApp();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const ingest = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      if (isDemo) {
        await new Promise((r) => setTimeout(r, 1500));
        setResult(mockIngestResponse);
      } else {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/api/v1/knowledge/ingest', {
          method: 'POST',
          body: formData,
        });
        if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
        const data = (await res.json()) as IngestResponse;
        setResult(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return { ingest, loading, result, error };
}
