import { InputHTMLAttributes, forwardRef } from 'react';

export interface CheckboxProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string;
  error?: string;
  helperText?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, error, helperText, className = '', id, ...props }, ref) => {
    const checkboxId = id || label.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="relative flex items-start">
        <div className="flex h-6 items-center">
          <input
            ref={ref}
            id={checkboxId}
            type="checkbox"
            className={`
              h-4 w-4 rounded border-gray-300
              text-primary-600 focus:ring-primary-600
              disabled:cursor-not-allowed disabled:opacity-50
              ${error ? 'border-error-500' : ''}
              ${className}
            `}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={
              error
                ? `${checkboxId}-error`
                : helperText
                  ? `${checkboxId}-helper`
                  : undefined
            }
            {...props}
          />
        </div>
        <div className="ml-3">
          <label
            htmlFor={checkboxId}
            className="text-sm font-medium text-gray-700"
          >
            {label}
          </label>
          {error && (
            <p id={`${checkboxId}-error`} className="text-sm text-error-600">
              {error}
            </p>
          )}
          {helperText && !error && (
            <p id={`${checkboxId}-helper`} className="text-sm text-gray-500">
              {helperText}
            </p>
          )}
        </div>
      </div>
    );
  }
);

Checkbox.displayName = 'Checkbox';

export default Checkbox;
