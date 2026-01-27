import { InputHTMLAttributes, forwardRef } from 'react';

export interface ToggleProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string;
  description?: string;
}

export const Toggle = forwardRef<HTMLInputElement, ToggleProps>(
  ({ label, description, className = '', id, checked, ...props }, ref) => {
    const toggleId = id || label.toLowerCase().replace(/\s+/g, '-');
    const labelId = `${toggleId}-label`;

    return (
      <div className="flex items-center justify-between">
        <div className="flex flex-col">
          <label
            id={labelId}
            htmlFor={toggleId}
            className="text-sm font-medium text-gray-700"
          >
            {label}
          </label>
          {description && (
            <span className="text-sm text-gray-500">{description}</span>
          )}
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={checked}
          aria-labelledby={labelId}
          onClick={() => {
            const input = document.getElementById(toggleId) as HTMLInputElement;
            if (input) {
              input.click();
            }
          }}
          className={`
            relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer
            rounded-full border-2 border-transparent transition-colors
            duration-200 ease-in-out focus:outline-none focus:ring-2
            focus:ring-primary-600 focus:ring-offset-2
            ${checked ? 'bg-primary-600' : 'bg-gray-200'}
            ${className}
          `}
        >
          <span
            className={`
              pointer-events-none inline-block h-5 w-5 transform rounded-full
              bg-white shadow ring-0 transition duration-200 ease-in-out
              ${checked ? 'translate-x-5' : 'translate-x-0'}
            `}
          />
        </button>
        <input
          ref={ref}
          id={toggleId}
          type="checkbox"
          checked={checked}
          className="sr-only"
          {...props}
        />
      </div>
    );
  }
);

Toggle.displayName = 'Toggle';

export default Toggle;
