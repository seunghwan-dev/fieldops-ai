interface Props {
  answer: string;
  sources: string[];
  meta: {
    vector_hits: number;
    bm25_hits: number;
    search_time_ms: number;
  };
}

export default function AnswerBox({ answer, sources, meta }: Props) {
  return (
    <div className="mt-6 bg-gray-100 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 animate-fade-in">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
        AI Answer
      </p>
      <p className="text-gray-900 dark:text-gray-100 text-sm leading-relaxed">
        {answer}
      </p>
      <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-700 flex flex-wrap items-center gap-2 font-mono text-xs text-gray-400">
        <span>{sources.length} sources</span>
        <span>·</span>
        <span>vector: {meta.vector_hits}</span>
        <span>·</span>
        <span>bm25: {meta.bm25_hits}</span>
        <span>·</span>
        <span>{meta.search_time_ms}ms</span>
      </div>
    </div>
  );
}
