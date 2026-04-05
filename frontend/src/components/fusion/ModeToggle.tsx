interface Props {
  mode: 'ml_only' | 'fusion';
  onToggle: (mode: 'ml_only' | 'fusion') => void;
}

export default function ModeToggle({ mode, onToggle }: Props) {
  return (
    <button
      onClick={() => onToggle(mode === 'ml_only' ? 'fusion' : 'ml_only')}
      className={`relative w-14 h-7 rounded-full transition-colors ${
        mode === 'fusion' ? 'bg-orange-500' : 'bg-gray-300 dark:bg-gray-600'
      }`}
      aria-label="Toggle fusion mode"
    >
      <span
        className={`absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full shadow transition-transform ${
          mode === 'fusion' ? 'translate-x-7' : ''
        }`}
      />
    </button>
  );
}
