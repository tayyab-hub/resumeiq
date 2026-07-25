import {
  forwardRef,
  useId,
  type InputHTMLAttributes,
  type ReactNode,
  type TextareaHTMLAttributes,
} from 'react';
import { cn } from '@/utilities/format';

interface FieldShellProps {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  children: ReactNode;
}

/**
 * Every input in the application is wrapped in this shell, so a labelled
 * control with an announced error message is the default rather than something
 * each form has to remember.
 */
function FieldShell({ id, label, hint, error, required, children }: FieldShellProps) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium text-ink-700">
        {label}
        {required && (
          <span className="ml-1 text-danger-600" aria-hidden="true">
            *
          </span>
        )}
        {required && <span className="sr-only"> (required)</span>}
      </label>
      {hint && (
        <p id={`${id}-hint`} className="text-xs text-ink-500">
          {hint}
        </p>
      )}
      {children}
      {error && (
        // role="alert" so the message is announced when it appears.
        <p id={`${id}-error`} role="alert" className="text-sm text-danger-600">
          {error}
        </p>
      )}
    </div>
  );
}

const CONTROL_CLASSES =
  'block w-full rounded border bg-white px-3 text-ink-900 placeholder:text-ink-400 ' +
  'transition-colors focus:border-brand-500 disabled:cursor-not-allowed disabled:bg-ink-100';

export interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string;
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, hint, error, className, id, required, ...rest },
  ref,
) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const describedBy =
    [hint ? `${fieldId}-hint` : null, error ? `${fieldId}-error` : null]
      .filter(Boolean)
      .join(' ') || undefined;

  return (
    <FieldShell id={fieldId} label={label} hint={hint} error={error} required={required}>
      <input
        ref={ref}
        id={fieldId}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(
          CONTROL_CLASSES,
          'h-11',
          error ? 'border-danger-500' : 'border-ink-300',
          className,
        )}
        {...rest}
      />
    </FieldShell>
  );
});

export interface TextAreaFieldProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  hint?: string;
  error?: string;
}

export const TextAreaField = forwardRef<HTMLTextAreaElement, TextAreaFieldProps>(
  function TextAreaField({ label, hint, error, className, id, required, ...rest }, ref) {
    const generatedId = useId();
    const fieldId = id ?? generatedId;
    const describedBy =
      [hint ? `${fieldId}-hint` : null, error ? `${fieldId}-error` : null]
        .filter(Boolean)
        .join(' ') || undefined;

    return (
      <FieldShell id={fieldId} label={label} hint={hint} error={error} required={required}>
        <textarea
          ref={ref}
          id={fieldId}
          required={required}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={cn(
            CONTROL_CLASSES,
            'py-2.5 leading-relaxed',
            error ? 'border-danger-500' : 'border-ink-300',
            className,
          )}
          {...rest}
        />
      </FieldShell>
    );
  },
);

export interface CheckboxFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
}

export const CheckboxField = forwardRef<HTMLInputElement, CheckboxFieldProps>(
  function CheckboxField({ label, hint, id, className, ...rest }, ref) {
    const generatedId = useId();
    const fieldId = id ?? generatedId;

    return (
      <div className="flex gap-3">
        <input
          ref={ref}
          id={fieldId}
          type="checkbox"
          aria-describedby={hint ? `${fieldId}-hint` : undefined}
          className={cn(
            'mt-0.5 h-5 w-5 shrink-0 rounded border-ink-300 text-brand-600',
            'focus:ring-brand-500',
            className,
          )}
          {...rest}
        />
        <div className="space-y-0.5">
          <label htmlFor={fieldId} className="block text-sm font-medium text-ink-700">
            {label}
          </label>
          {hint && (
            <p id={`${fieldId}-hint`} className="text-xs text-ink-500">
              {hint}
            </p>
          )}
        </div>
      </div>
    );
  },
);
