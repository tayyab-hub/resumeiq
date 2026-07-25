import { useRef, useState, type DragEvent } from 'react';
import { FileText, Upload, X } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { validateResumeFile } from '@/schemas/forms';
import { cn, formatBytes } from '@/utilities/format';

export interface FileUploadProps {
  file: File | null;
  onChange: (file: File | null) => void;
  error?: string | undefined;
}

/**
 * Drag-and-drop resume upload.
 *
 * Client-side checks here are for immediate feedback. The server repeats every
 * one of them, and additionally verifies the file's magic bytes — the only
 * check an attacker cannot defeat by renaming a file.
 */
export function FileUpload({ file, onChange, error }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const message = error ?? localError;

  function accept(candidate: File | null) {
    const problem = validateResumeFile(candidate);
    if (problem) {
      setLocalError(problem);
      onChange(null);
      return;
    }
    setLocalError(null);
    onChange(candidate);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    accept(event.dataTransfer.files?.[0] ?? null);
  }

  if (file) {
    return (
      <div className="space-y-1.5">
        <span className="block text-sm font-medium text-ink-700">Resume (PDF)</span>
        <div className="flex items-center gap-3 rounded-lg border border-ink-300 bg-white px-4 py-3">
          <FileText className="h-5 w-5 shrink-0 text-brand-600" aria-hidden="true" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-ink-900">{file.name}</p>
            <p className="text-xs text-ink-500">{formatBytes(file.size)}</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              onChange(null);
              setLocalError(null);
              if (inputRef.current) inputRef.current.value = '';
            }}
            aria-label={`Remove ${file.name}`}
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      <label htmlFor="resume-input" className="block text-sm font-medium text-ink-700">
        Resume (PDF)
        <span className="ml-1 text-danger-600" aria-hidden="true">
          *
        </span>
        <span className="sr-only"> (required)</span>
      </label>

      <div
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={cn(
          'rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors',
          isDragging ? 'border-brand-500 bg-brand-50' : 'border-ink-300 bg-white',
          message && 'border-danger-500',
        )}
      >
        <Upload className="mx-auto h-8 w-8 text-ink-400" aria-hidden="true" />
        <p className="mt-3 text-sm text-ink-600">
          Drag your PDF here, or{' '}
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="font-medium text-brand-700 underline underline-offset-2"
          >
            browse for a file
          </button>
        </p>
        <p className="mt-1 text-xs text-ink-500">PDF only, up to 5 MB</p>

        <input
          ref={inputRef}
          id="resume-input"
          type="file"
          accept="application/pdf,.pdf"
          className="sr-only"
          aria-describedby={message ? 'resume-input-error' : 'resume-input-hint'}
          aria-invalid={message ? true : undefined}
          onChange={(event) => accept(event.target.files?.[0] ?? null)}
        />
      </div>

      <p id="resume-input-hint" className="text-xs text-ink-500">
        Your file is analysed in memory and never saved. Only the analysis results are stored.
      </p>

      {message && (
        <p id="resume-input-error" role="alert" className="text-sm text-danger-600">
          {message}
        </p>
      )}
    </div>
  );
}
