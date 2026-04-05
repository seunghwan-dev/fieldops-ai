import { useDropzone } from 'react-dropzone';
import { Upload, Loader2 } from 'lucide-react';
import { useApp } from '../../contexts/AppContext';

interface Props {
  onUpload: (file: File) => void;
  loading: boolean;
}

export default function DropZone({ onUpload, loading }: Props) {
  const { t } = useApp();
  const { getRootProps, getInputProps, isDragActive, acceptedFiles } =
    useDropzone({
      accept: { 'application/pdf': ['.pdf'] },
      maxFiles: 1,
      disabled: loading,
      onDrop: (files) => {
        if (files[0]) onUpload(files[0]);
      },
    });

  return (
    <div
      {...getRootProps()}
      className={`mt-4 border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
        isDragActive
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
      } ${loading ? 'opacity-60 pointer-events-none' : ''}`}
    >
      <input {...getInputProps()} />
      {loading ? (
        <div className="flex flex-col items-center gap-2 text-blue-600">
          <Loader2 size={40} className="animate-spin" />
          <p className="font-medium">Processing PDF with VLM...</p>
          <p className="text-sm text-gray-500">
            {acceptedFiles[0]?.name}
          </p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 text-gray-500">
          <Upload size={40} />
          <p className="font-medium text-gray-700 dark:text-gray-300">
            {t.knowledge.dropzone}
          </p>
          <p className="text-sm">{t.knowledge.supported}</p>
        </div>
      )}
    </div>
  );
}
